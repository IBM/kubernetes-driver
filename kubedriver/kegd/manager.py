import uuid
import logging
from ignition.service.framework import Service, Capability
from kubedriver.kegd.model import (RemovalTask, RemovalTaskSettings, RemoveObjectAction, DeployTask, DeployHelmAction,
                                    DeployObjectsAction, DeployObjectAction, Labels, LabelValues, OutputExtractionTask,
                                    RemoveHelmAction, DeployHelmAction, ReadyCheckTask, RetrySettings,
                                    StrategyExecutionStates, V1alpha1KegdStrategyReportStatus, Tags, StrategyExecution, TaskGroup)
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.persistence import RecordNotFoundError
from kubedriver.kubeobjects import ObjectConfigurationDocument, InvalidObjectConfigurationDocumentError, InvalidObjectConfigurationError
from .exceptions import InvalidKegDeploymentStrategyError
from ignition.templating import TemplatingError
from .processor import KegdStrategyLocationProcessor
from ignition.service.logging import logging_context

logger = logging.getLogger(__name__)

class KegdStrategyManager(Service, Capability):

    def __init__(self, kegd_properties, context_factory, templating, job_queue):
        self.kegd_properties = kegd_properties
        self.context_factory = context_factory
        self.templating = templating
        self.job_queue = job_queue
        if self.kegd_properties.ready_checks.default_timeout_seconds == None:
            raise ValueError('Must set kegd.ready_checks.default_timeout_seconds in the configuration properties')
        if self.kegd_properties.ready_checks.default_timeout_seconds <= 0:
            raise ValueError('Must set kegd.ready_checks.default_timeout_seconds above zero in the configuration properties')
        if self.kegd_properties.ready_checks.max_timeout_seconds != None:
            if self.kegd_properties.ready_checks.default_timeout_seconds > self.kegd_properties.ready_checks.max_timeout_seconds:
                raise ValueError(f'Must set a value on kegd.ready_checks.default_timeout_seconds ({self.kegd_properties.ready_checks.default_timeout_seconds}) that is less than kegd.ready_checks.max_timeout_seconds ({self.kegd_properties.ready_checks.max_timeout_seconds}) in the configuration properties')

    def apply_kegd_strategy(self, kube_location, keg_name, kegd_strategy, operation_name, kegd_files, render_context):
        context = self.context_factory.build(kube_location)
        worker = KegdStrategyLocationManager(self.kegd_properties, context, self.templating)
        process_strategy_job = worker.build_process_strategy_job(keg_name, kegd_strategy, operation_name, kegd_files, render_context)
        job_data = {
            'job_type': ProcessStrategyJob.job_type,
            'data': process_strategy_job.on_write(),
            'logging_context': {k:v for k,v in logging_context.get_all().items()}
        }
        try:
            self.job_queue.queue_job(job_data)
        except Exception as e:
            #Try and delete the request as we never scheduled the job
            logger.exception(f'Failed to queue request \'{process_strategy_job.request_id}\', will attempt to remove report data')
            try:
                worker.delete_request_report(request_id)
            except Exception as nested:
                logger.exception(f'Failed to remove report for a request which failed to be queued: {process_strategy_job.request_id}')
            raise e from None
        return process_strategy_job.request_id

    def get_request_report(self, kube_location, request_id):
        context = self.context_factory.build(kube_location)
        worker = KegdStrategyLocationManager(self.kegd_properties, context, self.templating)
        return worker.get_request_report(request_id)

    def delete_request_report(self, kube_location, request_id):
        context = self.context_factory.build(kube_location)
        worker = KegdStrategyLocationManager(self.kegd_properties, context, self.templating)
        return worker.delete_request_report(request_id)

class KegdStrategyLocationManager:

    def __init__(self, kegd_properties, context, templating):
        self.kegd_properties = kegd_properties
        self.context = context
        self.kube_location = context.kube_location
        self.templating = templating
        self.keg_persister = context.keg_persister
        self.kegd_persister = context.kegd_persister
        self.api_ctl = context.api_ctl

    def build_process_strategy_job(self, keg_name, kegd_strategy, operation_name, kegd_files, render_context):
        keg_status = None
        try:
            keg_status = self.keg_persister.get(keg_name)
        except RecordNotFoundError:
            #Not found, first operation on this Keg 
            pass
        strategy_execution = self.__build_strategy_execution(kegd_strategy, operation_name, kegd_files, render_context, keg_status=keg_status)
        request_id = 'kegdr-' + str(uuid.uuid4())
        self.__create_report_status(request_id, keg_name, strategy_execution)
        return ProcessStrategyJob(request_id, self.kube_location, keg_name, strategy_execution, render_context)

    def get_request_report(self, request_id):
        return self.kegd_persister.get(request_id)

    def delete_request_report(self, request_id):
        try:
            return self.kegd_persister.delete(request_id)
        except RecordNotFoundError:
            #Not found, nothing to do
            pass

    def __create_report_status(self, request_id, keg_name, strategy_execution):
        report = V1alpha1KegdStrategyReportStatus()
        report.uid = request_id
        report.keg_name = keg_name
        report.operation = strategy_execution.operation_name
        report.task_groups = [task_group.name for task_group in strategy_execution.task_groups]
        report.run_cleanup = strategy_execution.run_cleanup
        report.state = StrategyExecutionStates.PENDING
        report.error = None
        labels = {
            Labels.MANAGED_BY: LabelValues.MANAGED_BY,
            Labels.KEG: keg_name
        }
        self.kegd_persister.create(request_id, report, labels=labels)
        return report

    def __gen_task_group_name(self, compose_script, render_context):
        uniqueness_string = None
        if compose_script.unique_by != None:
            if isinstance(compose_script.unique_by, str):
                uniqueness_string = self.templating.render('{{' + compose_script.unique_by + '}}', render_context)
            elif isinstance(compose_script.unique_by, list):
                for unique_by_param in compose_script.unique_by:
                    if uniqueness_string != None:
                        uniqueness_string += '::'
                    else:
                        uniqueness_string = ''
                    uniqueness_string += self.templating.render('{{' + unique_by_param + '}}', render_context)
        script_name = f'{compose_script.name}'
        if uniqueness_string is not None:
            script_name += f'::{uniqueness_string}'
        return script_name

    def __gen_removal_task_group_name(self, script_to_remove, render_context):
        original_script_exec_name = self.__gen_task_group_name(script_to_remove, render_context)
        return f'remove::{original_script_exec_name}'

    def __build_strategy_execution(self, kegd_strategy, operation_name, kegd_files, render_context, keg_status=None):
        task_groups = []
        ready_check_task = None
        output_extraction_task = None
        compose_script, scripts_to_remove = kegd_strategy.get_compose_scripts_for(operation_name)
        removal_task_groups = self.__build_removal_task_groups(scripts_to_remove, kegd_files, render_context, keg_status=keg_status)
        task_groups.extend(removal_task_groups)
        if compose_script != None:
            deploy_task_group = self.__build_deploy_task_group(compose_script, kegd_files, render_context)
            task_groups.append(deploy_task_group)
            if compose_script.ready_check != None:
                ready_check_task = self.__build_ready_check_task(compose_script, kegd_files)
            if compose_script.output_extraction != None:
                output_extraction_task = self.__build_output_extraction_task(compose_script, kegd_files)
        run_cleanup = False
        if kegd_strategy.cleanup_on == operation_name: 
            run_cleanup = True
        return StrategyExecution(operation_name, task_groups=task_groups, ready_check_task=ready_check_task, 
                                    output_extraction_task=output_extraction_task, run_cleanup=run_cleanup)

    def __build_removal_task_groups(self, scripts_to_remove, kegd_files, render_context, keg_status=None):
        task_groups = []
        if keg_status != None:
            for script_to_remove in scripts_to_remove:
                task_group_name = self.__gen_removal_task_group_name(script_to_remove, render_context)
                task_group = TaskGroup(task_group_name)
                task_groups.append(task_group)
                search_value = self.__gen_task_group_name(script_to_remove, render_context)
                objects, helm_releases = self.__find_composition_with_tag_value_in(keg_status, Tags.DEPLOYED_ON, search_value)
                for obj in objects:
                    task_group.removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveObjectAction(obj.group, obj.kind, obj.name, obj.namespace)))
                for helm_release in helm_releases:
                    task_group.removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveHelmAction(helm_release.name, namespace=helm_release.namespace)))
        return task_groups

    def __build_deploy_task_group(self, compose_script, kegd_files, render_context):
        task_group_name = self.__gen_task_group_name(compose_script, render_context)
        task_group = TaskGroup(task_group_name)
        for deploy_task in compose_script.deploy:
            if isinstance(deploy_task.action, DeployObjectsAction):
                task_group.deploy_tasks.extend(self.__expand_deploy_objects_action(deploy_task, kegd_files, render_context))
            elif isinstance(deploy_task.action, DeployHelmAction):
                task_group.deploy_tasks.extend(self.__expand_helm_action(deploy_task, kegd_files, render_context))
            else:
                task_group.deploy_tasks.append(deploy_task)
        return task_group

    def __build_ready_check_task(self, compose_script, kegd_files):
        ready_script_name = compose_script.ready_check.script
        file_path = kegd_files.get_script_file(ready_script_name)
        with open(file_path, 'r') as f:
            ready_script_content = f.read()
        retry_settings = compose_script.ready_check.retry_settings
        if retry_settings == None:
            retry_settings = RetrySettings()
        if retry_settings.max_attempts == None:
            retry_settings.max_attempts = self.kegd_properties.ready_checks.default_max_attempts
        if retry_settings.timeout_seconds == None:
            retry_settings.timeout_seconds = self.kegd_properties.ready_checks.default_timeout_seconds
        if retry_settings.interval_seconds == None:
            retry_settings.interval_seconds = self.kegd_properties.ready_checks.default_interval_seconds
        if self.kegd_properties.ready_checks.max_timeout_seconds != None and retry_settings.timeout_seconds > self.kegd_properties.ready_checks.max_timeout_seconds:
            logger.warning(f'Retry timeout seconds value of ({retry_settings.timeout_seconds}) is greater than the max timeout allowed ({self.kegd_properties.ready_checks.max_timeout_seconds}). The value will be reduced to the maximum.')
            retry_settings.timeout_seconds = self.kegd_properties.ready_checks.max_timeout_seconds
        if retry_settings.timeout_seconds <= 0:
            raise InvalidKegDeploymentStrategyError(f'timeout seconds value ({retry_settings.timeout_seconds}) must be greater than zero')
        return ReadyCheckTask(ready_script_content, ready_script_name, retry_settings)

    def __build_output_extraction_task(self, compose_script, kegd_files):
        output_script_name = compose_script.output_extraction.script
        file_path = kegd_files.get_script_file(output_script_name)
        with open(file_path, 'r') as f:
            output_script_content = f.read()
        return OutputExtractionTask(output_script_content, output_script_name)

    def __expand_helm_action(self, deploy_task, kegd_files, render_context):
        deploy_action = deploy_task.action
        if deploy_action.chart != None:
            deploy_action.chart = self.templating.render(deploy_action.chart, render_context)
            if kegd_files.has_helm_file(deploy_action.chart):
                deploy_action.chart = kegd_files.get_helm_file_base64(deploy_action.chart)
                deploy_action.chart_encoded = True
        if deploy_action.name != None:
            deploy_action.name = self.templating.render(deploy_action.name, render_context)
        if deploy_action.namespace != None:
            deploy_action.namespace = self.templating.render(deploy_action.namespace, render_context)
        if deploy_action.values != None:
            deploy_action.values = self.templating.render(deploy_action.values, render_context)
            values_file_path = kegd_files.get_helm_file(deploy_action.values)
            with open(values_file_path, 'r') as f:
                values_file_content = f.read()
            rendered_values_file_content = self.__process_template(values_file_content, render_context, values_file_path)
            deploy_action.values = rendered_values_file_content
        return [deploy_task]
    
    def __expand_deploy_objects_action(self, deploy_task, kegd_files, render_context):
        deploy_action = deploy_task.action
        if deploy_action.file != None:
            deploy_action.file = self.templating.render(deploy_action.file, render_context)
        tasks = []
        file_path = kegd_files.get_object_file(deploy_action.file)
        with open(file_path, 'r') as f:
            template = f.read()
        rendered_template = self.__process_template(template, render_context, file_path)
        objects_confs_in_template = self.__parse_doc_to_objects(rendered_template, file_path)
        for object_conf in objects_confs_in_template:
            group = object_conf.api_version
            kind = object_conf.kind
            name = object_conf.name
            namespace = object_conf.namespace
            if namespace == None and self.api_ctl.is_object_namespaced(group, kind):
                namespace = self.kube_location.default_object_namespace
            tasks.append(DeployTask(deploy_task.settings, DeployObjectAction(group, kind, name, object_conf.data, namespace=namespace)))
        return tasks

    def __find_composition_with_tag_value_in(self, keg_status, tag_key, tag_value):
        objects = []
        helm_releases = []
        if keg_status != None and keg_status.composition is not None:
            if keg_status.composition.objects is not None:
                for object_status in keg_status.composition.objects:
                    if object_status.tags != None and tag_value in object_status.tags.get(tag_key):
                        objects.append(object_status)
            if keg_status.composition.helm_releases is not None:
                for helm_status in keg_status.composition.helm_releases:
                    if helm_status.tags != None and tag_value in helm_status.tags.get(tag_key):
                        helm_releases.append(helm_status)
        return objects, helm_releases

    def __process_template(self, template, render_context, source_file_path):
        try:
            return self.templating.render(template, render_context)
        except TemplatingError as e:
            raise InvalidKegDeploymentStrategyError(f'Failed to render template {source_file_path}: {str(e)}') from e

    def __parse_doc_to_objects(self, doc_data, source_file_path):
        try:
            return ObjectConfigurationDocument(doc_data).read()
        except (InvalidObjectConfigurationDocumentError, InvalidObjectConfigurationError) as e:
            raise InvalidKegDeploymentStrategyError(f'Object configuration found in file {source_file_path} is invalid: {str(e)}') from e
            