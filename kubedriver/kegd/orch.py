import uuid
import logging
from ignition.service.framework import Service, Capability
from kubedriver.kegd.action_handlers import DeployObjectHandler, RemoveObjectHandler, DeployHelmHandler, RemoveHelmHandler
from kubedriver.keg.model import V1alpha1KegStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import (RemovalTask, RemovalTaskSettings, RemoveObjectAction, DeployTask, DeployHelmAction,
                                    DeployObjectsAction, DeployObjectAction, DeployTaskSettings, Labels, LabelValues, 
                                    RemoveHelmAction, DeployHelmAction,
                                    OperationStates, V1alpha1KegDeploymentReportStatus, Tags, OperationExecution, OperationScript)
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.persistence import PersistenceError, RecordNotFoundError
from kubedriver.kubeobjects import ObjectConfigurationDocument, ObjectConfigurationTemplate, InvalidObjectConfigurationDocumentError, InvalidObjectConfigurationError
from .exceptions import InvalidKegDeploymentStrategyError, StrategyProcessingError
from ignition.templating import TemplatingError

logger = logging.getLogger(__name__)

REMOVE_ACTION_HANDLERS = {
    RemoveObjectAction: RemoveObjectHandler(),
    RemoveHelmAction: RemoveHelmHandler()
}
DEPLOY_ACTION_HANDLERS = {
    DeployObjectAction: DeployObjectHandler(),
    DeployHelmAction: DeployHelmHandler()
}

class KegdOrchestrator(Service, Capability):

    def __init__(self, context_factory, templating, job_queue):
        self.context_factory = context_factory
        self.templating = templating
        self.job_queue = job_queue
        self.job_queue.register_job_handler(ProcessStrategyJob.job_type, self._handle_process_strategy_job)
    
    def apply_kegd_strategy(self, kube_location, keg_name, kegd_strategy, operation_name, kegd_files, render_context):
        context = self.context_factory.build(kube_location)
        worker = LocationWorker(context, self.templating)
        process_strategy_job = worker.build_process_strategy_job(keg_name, kegd_strategy, operation_name, kegd_files, render_context)
        job_data = {
            'job_type': ProcessStrategyJob.job_type,
            'data': process_strategy_job.on_write()
        }
        self.job_queue.queue_job(job_data)
        return process_strategy_job.request_id

    def get_request_report(self, kube_location, request_id):
        context = self.context_factory.build(kube_location)
        worker = LocationWorker(context, self.templating)
        return worker.get_request_report(request_id)

    def delete_request_report(self, kube_location, request_id):
        context = self.context_factory.build(kube_location)
        worker = LocationWorker(context, self.templating)
        return worker.delete_request_report(request_id)

    def _handle_process_strategy_job(self, job):
        job_data = job.get('data')
        process_strategy_job = ProcessStrategyJob.on_read(**job_data)
        context = self.context_factory.build(process_strategy_job.kube_location)
        worker = LocationWorker(context, self.templating)
        return worker.handle_process_strategy_job(process_strategy_job)

class LocationWorker:

    def __init__(self, context, templating):
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
        operation_execution = self.__build_operation_execution(kegd_strategy, operation_name, kegd_files, render_context, keg_status=keg_status)
        request_id = 'kegdr-' + str(uuid.uuid4())
        self.__create_report_status(request_id, keg_name, operation_execution)
        return ProcessStrategyJob(request_id, self.kube_location, keg_name, operation_execution)

    def get_request_report(self, request_id):
        return self.kegd_persister.get(request_id)

    def delete_request_report(self, request_id):
        try:
            return self.kegd_persister.delete(request_id)
        except RecordNotFoundError:
            #Not found, nothing to do
            pass

    def handle_process_strategy_job(self, process_strategy_job):
        logger.info(f'Processing request \'{process_strategy_job.request_id}\'')
        # Errors retrieving the request or checking request state result in the job not being requeued
        report_status = self.kegd_persister.get(process_strategy_job.request_id)
        # This point forward we must make best efforts to update the request if there is an error
        request_errors = None
        try:
            keg_name = process_strategy_job.keg_name
            keg_status = self.__get_or_init_keg(keg_name)
            for script in process_strategy_job.operation_execution.scripts:
                request_errors = self.__process_script(report_status, keg_name, keg_status, script)
                if len(request_errors) > 0:
                    break
            
            # Immediate cleanup 
            immediate_cleanup_errors = self.__process_immediate_cleanup(report_status, keg_name, keg_status, process_strategy_job.operation_execution.scripts, request_errors)
            request_errors.extend(immediate_cleanup_errors)

            # Keg cleanup - only if the request hasn't failed
            if len(request_errors) == 0 and process_strategy_job.operation_execution.run_cleanup:
                logger.debug(f'Cleaning out Keg \'{keg_name}\' on request \'{process_strategy_job.request_id}\'')
                cleanup_errors = self.__run_cleanup(report_status, keg_name, keg_status)
                request_errors.extend(cleanup_errors)
        except Exception as e:
            logger.exception(f'An error occurred whilst processing request \'{process_strategy_job.request_id}\' on group \'{process_strategy_job.keg_name}\', attempting to update records with failure')
            if request_errors == None:
                request_errors = []
            request_errors.append(f'Internal error: {str(e)}')
        # If we can't update the record then we can't do much else TODO: retry the request and/or update
        self.__update_report_with_results(report_status, request_errors)
        self.kegd_persister.update(process_strategy_job.request_id, report_status)
        return True

    def __process_immediate_cleanup(self, report_status, keg_name, keg_status, operation_scripts, request_errors):
        allowed_values = [DeployTaskSettings.IMMEDIATE_CLEANUP_ALWAYS]
        if len(request_errors) > 0:
            allowed_values.append(DeployTaskSettings.IMMEDIATE_CLEANUP_FAILURE)
        else:
            allowed_values.append(DeployTaskSettings.IMMEDIATE_CLEANUP_SUCCESS)
        removal_tasks = []
        for operation_script in operation_scripts:
            for deploy_task in operation_script.deploy_tasks:
                if deploy_task.settings.immediate_cleanup_on in allowed_values:
                    handler = self.__get_deploy_task_handler(deploy_task)
                    removal_task = handler.build_cleanup(deploy_task.action, deploy_task.settings)
                    removal_tasks.append(removal_task)
        if len(removal_tasks) > 0:
            return self.__process_removal_tasks(report_status, 'Immediate Cleanup', keg_name, keg_status, removal_tasks)
        else:
            return []

    def __update_report_with_results(self, report_status, request_errors):
        if request_errors != None and len(request_errors) > 0:
            report_status.state = OperationStates.FAILED
            report_status.error = self.__summarise_request_errors(request_errors)
        else:
            report_status.state = OperationStates.COMPLETE
            report_status.error = None
        
    def __summarise_request_errors(self, request_errors):
        error_msg = 'Request encountered {0} error(s):'.format(len(request_errors))
        for idx, error in enumerate(request_errors):
            error_msg += '\n\t{0} - {1}'.format(idx+1, error)
        return error_msg

    def __get_removal_task_handler(self, task):
        handler = REMOVE_ACTION_HANDLERS.get(task.action.__class__)
        if handler is None:
            raise StrategyProcessingError(f'Could not find a handler for remove task {task.action.__class__}')
        return handler

    def __get_deploy_task_handler(self, task):
        handler = DEPLOY_ACTION_HANDLERS.get(task.action.__class__)
        if handler is None:
            raise StrategyProcessingError(f'Could not find a handler for deploy task {task.action.__class__}')
        return handler

    def __run_cleanup(self, report_status, keg_name, keg_status):
        cleanup_errors = self.__cleanout_keg(report_status, keg_name, keg_status)
        if len(cleanup_errors) == 0:
            try:
                self.keg_persister.delete(keg_name)
            except PersistenceError as e:
                msg = f'Failed to remove Keg \'{keg_name}\' on request \'{report_status.uid}\''
                logger.exception(msg)
                cleanup_errors.append(msg + ': ' + str(e))
        return cleanup_errors
        
    def __cleanout_keg(self, report_status, keg_name, keg_status):
        removal_tasks = []
        for obj_status in keg_status.composition.objects:
            removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveObjectAction(obj_status.group, obj_status.kind, obj_status.name, obj_status.namespace)))
        for helm_status in keg_status.composition.helm_releases:
            removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveHelmAction(helm_status.name, helm_status.namespace)))
        if len(removal_tasks) > 0:
            return self.__process_removal_tasks(report_status, 'Cleanup', keg_name, keg_status, removal_tasks)
        else:
            return []

    def __process_script(self, report_status, keg_name, keg_status, operation_script):
        script_errors = self.__process_removal_tasks(report_status, operation_script.name, keg_name, keg_status, operation_script.removal_tasks)
        if len(script_errors) == 0:
            script_errors = self.__process_deploy_tasks(report_status, operation_script.name, keg_name, keg_status, operation_script.deploy_tasks)
        return script_errors

    def __process_removal_tasks(self, report_status, script_name, keg_name, keg_status, removal_tasks):
        task_errors = []
        if len(removal_tasks) > 0:
            for task in removal_tasks:
                logger.info('Processing decorate for remove task ' + str(task.on_write()))
                handler = self.__get_removal_task_handler(task)
                handler.decorate(task.action, task.settings, script_name, keg_name, keg_status)
            try:
                self.keg_persister.update(keg_name, keg_status)
            except PersistenceError as e:
                msg = f'Failed to update Keg \'{keg_name}\' with planned composition remove changes on request \'{report_status.uid}\''
                logger.exception(msg)
                task_errors.append(msg + ': ' + str(e))
            else:
                #Proceed with remove
                for task in removal_tasks:
                    logger.info('Processing handler for remove task ' + str(task.on_write()))
                    handler = self.__get_removal_task_handler(task)
                    handler_errors = handler.handle(task.action, task.settings, script_name, keg_name, keg_status, self.context)
                    task_errors.extend(handler_errors)
                try:
                    self.keg_persister.update(keg_name, keg_status)
                except PersistenceError as e:
                    msg = f'Failed to update Keg \'{keg_name}\' with composition remove changes on request \'{report_status.uid}\''
                    logger.exception(msg)
                    task_errors.append(msg + ': ' + str(e))
        return task_errors

    def __process_deploy_tasks(self, report_status, script_name, keg_name, keg_status, deploy_tasks):
        task_errors = []
        if len(deploy_tasks) > 0:
            for task in deploy_tasks:
                logger.info('Processing decorate for deploy task ' + str(task.on_write()))
                handler = self.__get_deploy_task_handler(task)
                handler.decorate(task.action, task.settings, script_name, keg_name, keg_status)
            try:
                self.keg_persister.update(keg_name, keg_status)
            except PersistenceError as e:
                msg = f'Failed to update Keg \'{keg_name}\' with planned composition deploy changes on request \'{report_status.uid}\''
                logger.exception(msg)
                task_errors.append(msg + ': ' + str(e))
            else:
                #Proceed with deploy
                for task in deploy_tasks:
                    logger.info('Processing handler for deploy task ' + str(task.on_write()))
                    handler = self.__get_deploy_task_handler(task)
                    handler_errors = handler.handle(task.action, task.settings, script_name, keg_name, keg_status, self.context)
                    task_errors.extend(handler_errors)
                try:
                    self.keg_persister.update(keg_name, keg_status)
                except PersistenceError as e:
                    msg = f'Failed to update Keg \'{keg_name}\' with composition deploy changes on request \'{report_status.uid}\''
                    logger.exception(msg)
                    task_errors.append(msg + ': ' + str(e))
        return task_errors

    def __get_or_init_keg(self, keg_name):
        try:
            keg = self.keg_persister.get(keg_name)
        except RecordNotFoundError:
            # Not found
            keg = V1alpha1KegStatus()
            keg.composition = V1alpha1KegCompositionStatus()
            keg.composition.objects = []
            keg.composition.helm_releases = []
            self.keg_persister.create(keg_name, keg)
        return keg

    def __create_report_status(self, request_id, keg_name, operation_execution):
        report = V1alpha1KegDeploymentReportStatus()
        report.uid = request_id
        report.keg_name = keg_name
        report.operation = operation_execution.operation_name
        report.included_scripts = [script.name for script in operation_execution.scripts]
        report.run_cleanup = operation_execution.run_cleanup
        report.state = OperationStates.PENDING
        report.error = None
        labels = {
            Labels.MANAGED_BY: LabelValues.MANAGED_BY,
            Labels.KEG: keg_name
        }
        self.kegd_persister.create(request_id, report, labels=labels)
        return report

    def __gen_operation_execution_name(self, compose_script):
        return f'{compose_script.name}'

    def __gen_operation_script_name(self, compose_script, render_context):
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

    def __gen_cleanup_operation_script_name(self, script_to_reverse, render_context):
        original_script_exec_name = self.__gen_operation_script_name(script_to_reverse, render_context)
        return f'cleanup::{original_script_exec_name}'

    def __build_operation_execution(self, kegd_strategy, operation_name, kegd_files, render_context, keg_status=None):
        compose_script, scripts_to_cleanup = kegd_strategy.get_compose_scripts_for(operation_name)
        all_scripts = []
        cleanup_scripts = self.__build_cleanup_scripts(scripts_to_cleanup, kegd_files, render_context, keg_status=keg_status)
        all_scripts.extend(cleanup_scripts)
        if compose_script != None:
            compose_operation_script = self.__build_operation_script(compose_script, kegd_files, render_context)
            all_scripts.append(compose_operation_script)
        run_cleanup = False
        if kegd_strategy.cleanup_on == operation_name: 
            run_cleanup = True
        return OperationExecution(operation_name, scripts=all_scripts, run_cleanup=run_cleanup)

    def __build_cleanup_scripts(self, scripts_to_cleanup, kegd_files, render_context, keg_status=None):
        cleanup_scripts = []
        if keg_status != None:
            for script_to_reverse in scripts_to_cleanup:
                cleanup_script_name = self.__gen_cleanup_operation_script_name(script_to_reverse, render_context)
                cleanup_script = OperationScript(cleanup_script_name)
                cleanup_scripts.append(cleanup_script)
                search_value = self.__gen_operation_script_name(script_to_reverse, render_context)
                objects, helm_releases = self.__find_composition_with_tag_value_in(keg_status, Tags.DEPLOYED_ON, search_value)
                for obj in objects:
                    cleanup_script.removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveObjectAction(obj.group, obj.kind, obj.name, obj.namespace)))
                for helm_release in helm_releases:
                    cleanup_script.removal_tasks.append(RemovalTask(RemovalTaskSettings(), RemoveHelmAction(helm_release.name, namespace=helm_release.namespace)))
        return cleanup_scripts

    def __build_operation_script(self, compose_script, kegd_files, render_context):
        script_name = self.__gen_operation_script_name(compose_script, render_context)
        script = OperationScript(script_name)
        for deploy_task in compose_script.deploy:
            if isinstance(deploy_task.action, DeployObjectsAction):
                script.deploy_tasks.extend(self.__expand_deploy_objects_action(deploy_task, kegd_files, render_context))
            elif isinstance(deploy_task.action, DeployHelmAction):
                script.deploy_tasks.extend(self.__expand_helm_action(deploy_task, kegd_files, render_context))
            else:
                script.deploy_tasks.append(deploy_task)
        return script

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
            