import logging
from ignition.service.framework import Service, Capability
from kubedriver.kegd.action_handlers import DeployObjectHandler, RemoveObjectHandler, DeployHelmHandler, RemoveHelmHandler, ReadyCheckHandler
from kubedriver.keg.model import V1alpha1KegStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import (RemovalTask, RemovalTaskSettings, RemoveObjectAction, DeployTask, DeployHelmAction,
                                    DeployObjectAction, DeployTaskSettings,
                                    RemoveHelmAction, DeployHelmAction, ReadyCheckTask,
                                    StrategyExecutionStates, StrategyExecutionPhases)
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.persistence import PersistenceError, RecordNotFoundError
from .exceptions import StrategyProcessingError, MultiErrorStrategyProcessingError

logger = logging.getLogger(__name__)

REMOVE_ACTION_HANDLERS = {
    RemoveObjectAction: RemoveObjectHandler(),
    RemoveHelmAction: RemoveHelmHandler()
}
DEPLOY_ACTION_HANDLERS = {
    DeployObjectAction: DeployObjectHandler(),
    DeployHelmAction: DeployHelmHandler()
}

PHASES = [
    StrategyExecutionPhases.TASKS, 
    StrategyExecutionPhases.READY_CHECK,
    StrategyExecutionPhases.OUTPUTS,
    StrategyExecutionPhases.IMMEDIATE_CLEANUP,
    StrategyExecutionPhases.CLEANUP
]

class QueueManager:

    def __init__(self, job_queue):
        self.job_queue = job_queue

class KegdStrategyProcessor(Service, Capability):

    def __init__(self, context_factory, templating, job_queue):
        self.context_factory = context_factory
        self.templating = templating
        self.job_queue = job_queue
        self.job_queue.register_job_handler(ProcessStrategyJob.job_type, self.handle_process_strategy_job)
    
    def handle_process_strategy_job(self, job):
        job_data = job.get('data')
        process_strategy_job = ProcessStrategyJob.on_read(**job_data)
        context = self.context_factory.build(process_strategy_job.kube_location)
        worker = KegdStrategyLocationProcessor(context, self.templating, QueueManager(self.job_queue))
        return worker.handle_process_strategy_job(process_strategy_job)

class PhaseResult:

    def __init__(self, errors=None, requeue=False):
        self.errors = errors if errors is not None else []
        self.requeue = requeue

class KegdStrategyLocationProcessor:

    def __init__(self, context, templating, queue_manager):
        self.context = context
        self.kube_location = context.kube_location
        self.templating = templating
        self.keg_persister = context.keg_persister
        self.kegd_persister = context.kegd_persister
        self.api_ctl = context.api_ctl
        self.queue_manager = queue_manager

    def handle_process_strategy_job(self, process_strategy_job):
        logger.info(f'Processing request \'{process_strategy_job.request_id}\'')
        # Errors retrieving the request or checking request state result in the job not being requeued
        strategy_execution = process_strategy_job.strategy_execution
        report_status = self.kegd_persister.get(process_strategy_job.request_id)
        # TODO Request not found?
        if report_status.state != StrategyExecutionStates.RUNNING:
            report_status.state = StrategyExecutionStates.RUNNING
            self.kegd_persister.update(report_status.uid, report_status)
        # This point forward we must make best efforts to update the request if there is an error
        phase_result = None
        errors = []
        try:
            if report_status.phase == None:
                report_status.phase = StrategyExecutionPhases.TASKS
            keg_name = process_strategy_job.keg_name
            phase_result = self.__process_next_phases(report_status, keg_name, strategy_execution, process_strategy_job.resource_context_properties)
            if phase_result.requeue:
                logger.info('RETURN FALSE TO REQ')
                return False
        except Exception as e:
            logger.exception(f'An error occurred whilst processing deployment strategy \'{report_status.uid}\' on group \'{process_strategy_job.keg_name}\', attempting to update records with failure')
            if isinstance(e, MultiErrorStrategyProcessingError):
                errors.extend(e.original_errors)
            errors.append(f'Internal error: {str(e)}')

        # If we can't update the record then we can't do much else TODO: retry the request and/or update?
        if phase_result != None:
            errors.extend(phase_result.errors)
        self.__update_report_with_final_results(report_status, errors)
        return True

    def __process_next_phases(self, report_status, keg_name, strategy_execution, resource_context_properties):
        keg_status = self.__get_or_init_keg(keg_name)
        all_errors = []
        try:
            # This point forward we must make best efforts to update the request if there is an error (and to run Immediate cleanup on error)
            while report_status.phase != None and report_status.phase != StrategyExecutionPhases.END:
                phase_result = None
                try:
                    if report_status.phase == StrategyExecutionPhases.TASKS:
                        phase_result = self.__execute_task_groups(report_status, keg_name, keg_status, strategy_execution)
                    elif report_status.phase == StrategyExecutionPhases.READY_CHECK:
                        phase_result = self.__execute_ready_check_task(report_status, keg_name, keg_status, strategy_execution, resource_context_properties)
                    elif report_status.phase == StrategyExecutionPhases.OUTPUTS:
                        phase_result = PhaseResult()
                    elif report_status.phase == StrategyExecutionPhases.IMMEDIATE_CLEANUP or report_status.phase == StrategyExecutionPhases.IMMEDIATE_CLEANUP_ON_FAILURE:
                        phase_result = self.__process_immediate_cleanup(report_status, keg_name, keg_status, strategy_execution, all_errors)
                    elif report_status.phase == StrategyExecutionPhases.CLEANUP:
                        phase_result = self.__execute_cleanup(report_status, keg_name, keg_status, strategy_execution)
                except Exception as e:
                    logger.exception(f'An error occurred whilst processing phase \'{report_status.phase}\' of deployment strategy \'{report_status.uid}\' on group \'{keg_name}\'')
                    phase_result = PhaseResult(errors=[str(e)])

                if phase_result.requeue:
                    logger.info('REQUEUE')
                    return phase_result
                else:
                    all_errors.extend(phase_result.errors)
                    # Even if there are errors, we may move to the Immediate cleanup stage on failure
                    self.__move_to_next_phase(report_status, strategy_execution, all_errors)
        except Exception as e:
            # Fail safe catch all, that makes sure we don't lose any of the original errors 
            if len(all_errors) > 0:
                logger.exception(f'An error occurred whilst processing phases of the deployment strategy \'{report_status.uid}\' on group \'{keg_name}\'')
                all_errors.append(str(e))
                raise MultiErrorStrategyProcessingError(str(e), all_errors) from e
            else:
                raise

        return PhaseResult(errors=all_errors)

    def __move_to_next_phase(self, report_status, strategy_execution, current_errors):
        next_phase = None
        if report_status.phase == StrategyExecutionPhases.IMMEDIATE_CLEANUP_ON_FAILURE:
            next_phase = StrategyExecutionPhases.END
        elif len(current_errors) > 0:
            immediate_cleanup_num = PHASES.index(StrategyExecutionPhases.IMMEDIATE_CLEANUP)
            phase_num = PHASES.index(report_status.phase)
            if phase_num < immediate_cleanup_num:
                next_phase = StrategyExecutionPhases.IMMEDIATE_CLEANUP_ON_FAILURE
                # Update with errors so we don't lose them in case this request is dropped and picked up by another node
                if report_status.errors == None:
                    report_status.errors = []
                report_status.errors.extend(current_errors)
            else:
                next_phase = StrategyExecutionPhases.END
        else:
            phase_num = PHASES.index(report_status.phase)
            next_phase_num = phase_num + 1
            if next_phase_num < len(PHASES):
                next_phase = PHASES[next_phase_num]
            else:
                next_phase = StrategyExecutionPhases.END
        report_status.phase = next_phase
        self.kegd_persister.update(report_status.uid, report_status)

    def __execute_task_groups(self, report_status, keg_name, keg_status, strategy_execution):
        errors = []
        for task_group in strategy_execution.task_groups:
            errors = self.__execute_task_group(report_status, keg_name, keg_status, task_group)
            if len(errors) > 0:
                break
        return PhaseResult(errors=errors)

    def __execute_task_group(self, report_status, keg_name, keg_status, task_group):
        errors = self.__process_removal_tasks(report_status, keg_name, keg_status, task_group.name, task_group.removal_tasks)
        if len(errors) == 0:
            errors = self.__process_deploy_tasks(report_status, keg_name, keg_status, task_group.name, task_group.deploy_tasks)
        return errors

    def __process_removal_tasks(self, report_status, keg_name, keg_status, task_group_name, removal_tasks):
        task_errors = []
        if len(removal_tasks) > 0:
            for task in removal_tasks:
                logger.info('Processing decorate for remove task ' + str(task.on_write()))
                handler = self.__get_removal_task_handler(task)
                handler.decorate(task.action, task.settings, task_group_name, keg_name, keg_status)
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
                    handler_errors = handler.handle(task.action, task.settings, task_group_name, keg_name, keg_status, self.context)
                    task_errors.extend(handler_errors)
                try:
                    self.keg_persister.update(keg_name, keg_status)
                except PersistenceError as e:
                    msg = f'Failed to update Keg \'{keg_name}\' with composition remove changes on request \'{report_status.uid}\''
                    logger.exception(msg)
                    task_errors.append(msg + ': ' + str(e))
        return task_errors

    def __process_deploy_tasks(self, report_status, keg_name, keg_status, task_group_name, deploy_tasks):
        task_errors = []
        if len(deploy_tasks) > 0:
            for task in deploy_tasks:
                logger.info('Processing decorate for deploy task ' + str(task.on_write()))
                handler = self.__get_deploy_task_handler(task)
                handler.decorate(task.action, task.settings, task_group_name, keg_name, keg_status)
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
                    handler_errors = handler.handle(task.action, task.settings, task_group_name, keg_name, keg_status, self.context)
                    task_errors.extend(handler_errors)
                try:
                    self.keg_persister.update(keg_name, keg_status)
                except PersistenceError as e:
                    msg = f'Failed to update Keg \'{keg_name}\' with composition deploy changes on request \'{report_status.uid}\''
                    logger.exception(msg)
                    task_errors.append(msg + ': ' + str(e))
        return task_errors

    def __execute_ready_check_task(self, report_status, keg_name, keg_status, strategy_execution, resource_context_properties):
        errors = []
        requeue = False
        if strategy_execution.ready_check_task != None:
            ready_check_task = strategy_execution.ready_check_task
            handler = ReadyCheckHandler()
            ready_result = handler.handle(report_status.operation, keg_name, keg_status, self.context, ready_check_task, resource_context_properties)
            has_failed, reason = ready_result.has_failed()
            if has_failed:
                errors.append(reason)
            elif not ready_result.is_ready():
                requeue = True
        return PhaseResult(errors=errors, requeue=requeue)

    def __process_immediate_cleanup(self, report_status, keg_name, keg_status, strategy_execution, exec_errors):
        allowed_values = [DeployTaskSettings.IMMEDIATE_CLEANUP_ALWAYS]
        if len(exec_errors) > 0:
            allowed_values.append(DeployTaskSettings.IMMEDIATE_CLEANUP_FAILURE)
        else:
            allowed_values.append(DeployTaskSettings.IMMEDIATE_CLEANUP_SUCCESS)
        removal_tasks = []
        for task_group in strategy_execution.task_groups:
            for deploy_task in task_group.deploy_tasks:
                if deploy_task.settings.immediate_cleanup_on in allowed_values:
                    handler = self.__get_deploy_task_handler(deploy_task)
                    removal_task = handler.build_cleanup(deploy_task.action, deploy_task.settings)
                    removal_tasks.append(removal_task)
        if len(removal_tasks) > 0:
            errors = self.__process_removal_tasks(report_status, keg_name, keg_status, 'Immediate Cleanup', removal_tasks)
            return PhaseResult(errors=errors)
        else:
            return PhaseResult()

    def __update_report_with_final_results(self, report_status, exec_errors):
        if exec_errors != None and len(exec_errors) > 0:
            report_status.state = StrategyExecutionStates.FAILED
            if report_status.errors == None:
                report_status.errors = []
            report_status.errors.extend(exec_errors)
        elif report_status.errors != None and len(report_status.errors) > 0:
            report_status.state = StrategyExecutionStates.FAILED
        else:
            report_status.state = StrategyExecutionStates.COMPLETE
            report_status.phase = StrategyExecutionPhases.END
            report_status.errors = []
        self.kegd_persister.update(report_status.uid, report_status)
 
    def __summarise_exec_errors(self, exec_errors):
        error_msg = 'Request encountered {0} error(s):'.format(len(exec_errors))
        for idx, error in enumerate(exec_errors):
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

    def __execute_cleanup(self, report_status, keg_name, keg_status, strategy_execution):
        cleanup_errors = []
        if strategy_execution.run_cleanup:
            cleanup_errors = self.__cleanout_keg(report_status, keg_name, keg_status)
            if len(cleanup_errors) == 0:
                try:
                    self.keg_persister.delete(keg_name)
                except PersistenceError as e:
                    msg = f'Failed to remove Keg \'{keg_name}\' on request \'{report_status.uid}\''
                    logger.exception(msg)
                    cleanup_errors.append(msg + ': ' + str(e))
        return PhaseResult(errors=cleanup_errors)
        
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