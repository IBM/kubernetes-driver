import uuid
import logging
import kubedriver.keg.model as keg_model
import kubedriver.kegd.model as kegd_model
from kubedriver.kegd.action_handlers import DeployObjectHandler, WithdrawObjectHandler
from kubedriver.kegd.model import (WithdrawTask, WithdrawTaskSettings, WithdrawObjectAction, DeployTask, DeployHelmAction,
                                    DeployObjectsAction, DeployObjectAction, Labels, LabelValues, OperationStates)
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.persistence import PersistenceError, RecordNotFoundError
from kubedriver.kubeobjects import ObjectConfigurationDocument, ObjectConfigurationTemplate, InvalidObjectConfigurationDocumentError, InvalidObjectConfigurationError
from .exceptions import InvalidKegDeploymentStrategyError, StrategyProcessingError
from ignition.templating import TemplatingError

logger = logging.getLogger(__name__)

WITHDRAW_ACTION_HANDLERS = {
    WithdrawObjectAction: WithdrawObjectHandler()
}
DEPLOY_ACTION_HANDLERS = {
    DeployObjectAction: DeployObjectHandler()
}

class KegdOrchestrator:

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

    def _handle_process_strategy_job(self, job):
        job_data = job.get('data')
        process_strategy_job = ProcessStrategyJob.on_read(**job_data)
        context = self.context_factory.build(process_strategy_job.kube_location)
        worker = LocationWorker(context, self.templating)
        return worker.handle_process_strategy_job(process_strategy_job)

class LocationWorker:

    def __init__(self, context, templating):
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
        operation_exec_name, withdraw_tasks, deploy_tasks = self.__determine_tasks(kegd_strategy, operation_name, kegd_files, render_context, keg_status=keg_status)
        request_id = 'kegdr-' + str(uuid.uuid4())
        self.__create_report_status(request_id, keg_name, operation_exec_name)
        return ProcessStrategyJob(request_id, self.kube_location, keg_name, operation_name, withdraw_tasks, deploy_tasks)

    def get_request_report(self, request_id):
        return self.kegd_persister.get(request_id)

    def handle_process_strategy_job(self, process_strategy_job):
        # Errors retrieving the request or checking request state result in the job not being requeued
        report_status = self.kegd_persister.get(process_strategy_job.request_id)
        # This point forward we must make best efforts to update the request if there is an error
        request_errors = []
        try:
            keg_status = self.__get_or_init_keg(process_strategy_job.keg_name)
            withdraw_errors = self.__process_withdraw_tasks(report_status, process_strategy_job.keg_name, keg_status, process_strategy_job.withdraw_tasks)
            if len(withdraw_errors) == 0:
                deploy_errors = self.__process_deploy_tasks(report_status, process_strategy_job.keg_name, keg_status, process_strategy_job.withdraw_tasks)
                request_errors.extend(deploy_errors)
            else:
                request_errors.extend(withdraw_errors)
        except Exception as e:
            logger.exception(f'An error occurred whilst processing request \'{process_strategy_job.request_id}\' on group \'{process_strategy_job.keg_name}\', attempting to update records with failure')
            request_errors.append(f'Internal error: {str(e)}')
        # If we can't update the record then we can't do much else TODO: retry the request and/or update
        self.__update_report_with_results(report_status, request_errors)
        return True

    def __update_report_with_results(self, report_status, request_errors):
        if len(request_errors) > 0:
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

    def __get_withdraw_task_handler(self, task):
        handler = WITHDRAW_ACTION_HANDLERS.get(task.action.__class__)
        if handler is None:
            raise StrategyProcessingError(f'Could not find a handler for withdraw task {task.action.__class__}')
        return handler

    def __get_deploy_task_handler(self, task):
        handler = DEPLOY_ACTION_HANDLERS.get(task.action.__class__)
        if handler is None:
            raise StrategyProcessingError(f'Could not find a handler for deploy task {task.action.__class__}')
        return handler

    def __process_withdraw_tasks(self, report_status, keg_name, keg_status, withdraw_tasks):
        task_errors = []
        if len(withdraw_tasks) > 0:
            for task in withdraw_tasks:
                handler = self.__get_withdraw_task_handler(task)
                handler.decorate(task.action, task.settings, report_status.operation, keg_name, keg_status)
            try:
                self.keg_persister.update(keg_name, keg_status)
            except PersistenceError as e:
                msg = f'Failed to update Keg \'{keg_name}\' with planned composition withdraw changes on request \'{report_status.uid}\''
                logger.exception(msg)
                task_errors.append(msg + ': ' + str(e))
            else:
                #Proceed with withdraw
                for task in withdraw_tasks:
                    handler = self.__get_withdraw_task_handler(task)
                    handler_errors = handler.handle(task.action, task.settings, report_status.operation, keg_name, keg_status, self.api_ctl)
                    task_errors.extend(handler_errors)
                try:
                    self.keg_persister.update(keg_name, keg_status)
                except PersistenceError as e:
                    msg = f'Failed to update Keg \'{keg_name}\' with composition withdraw changes on request \'{report_status.uid}\''
                    logger.exception(msg)
                    task_errors.append(msg + ': ' + str(e))
        return task_errors

    def __process_deploy_tasks(self, report_status, keg_name, keg_status, deploy_tasks):
        task_errors = []
        if len(deploy_tasks) > 0:
            for task in deploy_tasks:
                handler = self.__get_deploy_task_handler(task)
                handler.decorate(task.action, task.settings, report_status.operation, keg_name, keg_status)
            try:
                self.keg_persister.update(keg_name, keg_status)
            except PersistenceError as e:
                msg = f'Failed to update Keg \'{keg_name}\' with planned composition deploy changes on request \'{report_status.uid}\''
                logger.exception(msg)
                task_errors.append(msg + ': ' + str(e))
            else:
                #Proceed with deploy
                for task in deploy_tasks:
                    handler = self.__get_deploy_task_handler(task)
                    handler_errors = handler.handle(task.action, task.settings, report_status.operation, keg_name, keg_status, self.api_ctl)
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
            keg = keg_model.V1alpha1KegStatus()
            keg.composition = keg_model.V1alpha1KegCompositionStatus()
            keg.composition.objects = []
            keg.composition.helm_releases = []
        return keg

    def __create_report_status(self, request_id, keg_name, operation_exec_name):
        report = kegd_model.V1alpha1KegDeploymentReportStatus()
        report.uid = request_id
        report.keg_name = keg_name
        report.operation = operation_exec_name
        report.state = kegd_model.OperationStates.PENDING
        report.error = None
        labels = {
            Labels.MANAGED_BY: kegd_model.LabelValues.MANAGED_BY,
            Labels.KEG: keg_name
        }
        self.kegd_persister.create(request_id, report, labels=labels)
        return report

    def __gen_operation_execution_name(self, compose_script):
        return f'{compose_script.name}'

    def __determine_tasks(self, kegd_strategy, operation_name, kegd_files, render_context, keg_status=None):
        compose_script, reverse_scripts = kegd_strategy.get_compose_scripts_for(operation_name)
        operation_exec_name = self.__gen_operation_execution_name(compose_script)
        withdraw_tasks = self.__determine_reverse_tasks(operation_exec_name, reverse_scripts, kegd_files, render_context, keg_status=keg_status)
        deploy_tasks = self.__determine_deploy_tasks(operation_exec_name, compose_script, kegd_files, render_context)
        return (operation_exec_name, withdraw_tasks, deploy_tasks)

    def __determine_reverse_tasks(self, operation_exec_name, reverse_scripts, kegd_files, render_context, keg_status=None):
        tasks = []
        if keg_status != None:
            for reversed_script in reverse_scripts:
                search_value = self.__gen_operation_execution_name(reversed_script.name)
                objects = self.__find_composition_with_tag_value_in(keg_status, kegd_model.Tags.DEPLOYED_ON, search_value)
                for obj in objects:
                    tasks.append(WithdrawTask(WithdrawTaskSettings(), WithdrawObjectAction(obj.group, obj.kind, obj.name, obj.namespace)))
        return tasks

    def __determine_deploy_tasks(self, operation_exec_name, compose_script, kegd_files, render_context):
        tasks = []
        for deploy_task in compose_script.deploy:
            if isinstance(deploy_task.action, DeployObjectsAction):
                tasks.extend(self.__expand_deploy_objects_action(operation_exec_name, deploy_task, kegd_files, render_context))
        return tasks

    def __expand_deploy_objects_action(self, operation_exec_name, deploy_task, kegd_files, render_context):
        deploy_action = deploy_task.action
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
            if namespace == None and self.keg_persister.api_ctl.is_object_namespaced(group, kind):
                namespace = self.kube_location.default_object_namespace
            tasks.append(DeployTask(deploy_task.settings, DeployObjectAction(group, kind, name, object_conf.data, namespace=namespace)))
        return tasks

    def __find_composition_with_tag_value_in(self, keg_status, tag_key, tag_value):
        objects = []
        if keg_status != None and keg_status.composition is not None:
            if keg_status.composition.objects is not None:
                for object_status in keg_status.composition.objects:
                    if object_status.tag != None and tag_value in object_status.tag.get(tag_key):
                        objects.append(object_status)
        return objects

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
            