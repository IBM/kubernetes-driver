import logging
from ignition.service.framework import Service, Capability
from ignition.service.logging import logging_context
from kubedriver.kegd.action_handlers import (DeployObjectHandler, RemoveObjectHandler, DeployHelmHandler, 
                                                RemoveHelmHandler, ReadyCheckHandler, OutputExtractionHandler)
from kubedriver.keg.model import V1alpha1KegStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import (RemovalTask, RemovalTaskSettings, RemoveObjectAction, DeployTask, DeployHelmAction,
                                    DeployObjectAction, DeployTaskSettings, RetryStatus,
                                    RemoveHelmAction, DeployHelmAction, ReadyCheckTask,
                                    StrategyExecutionStates, StrategyExecutionPhases)
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.persistence import PersistenceError, RecordNotFoundError
from .exceptions import StrategyProcessingError, MultiErrorStrategyProcessingError
import kubedriver.utils.time as timeutil

logger = logging.getLogger(__name__)

REMOVE_ACTION_HANDLERS = {
    RemoveObjectAction: RemoveObjectHandler(),
    RemoveHelmAction: RemoveHelmHandler()
}
DEPLOY_ACTION_HANDLERS = {
    DeployObjectAction: DeployObjectHandler(),
    DeployHelmAction: DeployHelmHandler()
}

NORMAL_PHASE_ORDER = [
    StrategyExecutionPhases.TASKS, 
    StrategyExecutionPhases.READY_CHECK,
    StrategyExecutionPhases.OUTPUTS,
    StrategyExecutionPhases.IMMEDIATE_CLEANUP,
    StrategyExecutionPhases.CLEANUP
]

class KegdStrategyProcessor(Service, Capability):

    def __init__(self, context_factory, templating, job_queue):
        self.context_factory = context_factory
        self.templating = templating
        self.job_queue = job_queue
        self.job_queue.register_job_handler(ProcessStrategyJob.job_type, self.handle_process_strategy_job)
    
    def handle_process_strategy_job(self, job):
        try:
            logging_context.set_from_dict(job.get('logging_context', {}))
            job_data = job.get('data')
            process_strategy_job = ProcessStrategyJob.on_read(**job_data)
            context = self.context_factory.build(process_strategy_job.kube_location)
            worker = KegdStrategyLocationProcessor(context, self.templating)
            finished = worker.handle_process_strategy_job(process_strategy_job)
            if not finished:
                job['data'] = process_strategy_job.on_write()
            return finished
        finally:
            logging_context.clear()

class PhaseResult:

    def __init__(self, errors=None, requeue=None):
        self.errors = errors if errors is not None else []
        self.requeue = requeue

class RequeueRequest:

    def __init__(self, task_name, settings):
        self.task_name = task_name
        self.settings = settings

class KegdStrategyLocationProcessor:

    def __init__(self, context, templating):
        self.context = context
        self.kube_location = context.kube_location
        self.templating = templating
        self.keg_persister = context.keg_persister
        self.kegd_persister = context.kegd_persister
        self.api_ctl = context.api_ctl

    def handle_process_strategy_job(self, process_strategy_job):
        logger.debug(f'Processing request \'{process_strategy_job.request_id}\'')

        cancel_process, errors, requeue_process = self.__check_retry_status(process_strategy_job)
        if requeue_process:
            # Not finished == False
            return False
        
        # Errors retrieving the request or checking request state result in the job not being requeued
        strategy_execution = process_strategy_job.strategy_execution
        try:
            report_status = self.kegd_persister.get(process_strategy_job.request_id)
        except RecordNotFoundError as e:
            logger.exception(f'Report could not be found for request {process_strategy_job.request_id}, this request will no longer be processed')
            # Finished
            return True

        # This point forward we must make best efforts to update the request if there is an error
        if not cancel_process:
            self.__mark_as_running(report_status)
            phase_result = None
            try:
                if report_status.phase == None:
                    report_status.phase = StrategyExecutionPhases.TASKS
                keg_name = process_strategy_job.keg_name
                phase_result = self.__process_next_phases(report_status, keg_name, strategy_execution, process_strategy_job.resource_context_properties)
                if phase_result.requeue != None:
                    self.__update_retry_status(timeutil.utc_to_string(timeutil.get_utc_datetime()), process_strategy_job, phase_result.requeue)
                    if self.__has_exceeded_max_attempts(process_strategy_job.retry_status):
                        errors.append(f'Retryable task {process_strategy_job.retry_status.current_task} has exceeded max attempts of {process_strategy_job.retry_status.settings.max_attempts} (attempts {process_strategy_job.retry_status.attempts})')
                    else:
                        # Requeue
                        return False
                else:
                    self.__clear_retry_status(process_strategy_job)
            except Exception as e:
                logger.exception(f'An error occurred whilst processing deployment strategy \'{report_status.uid}\' on group \'{process_strategy_job.keg_name}\', attempting to update records with failure')
                if isinstance(e, MultiErrorStrategyProcessingError):
                    errors.extend(e.original_errors)
                errors.append(f'Internal error: {str(e)}')
            if phase_result != None:
                errors.extend(phase_result.errors)

        # If we can't update the record then the job is lost
        self.__update_report_with_final_results(report_status, errors)
        return True

    def __has_retry_timedout(self, now_as_datetime, retry_status):
        if retry_status == None:
            return False, None
        if retry_status.start_time == None:
            return False, None
        if retry_status.settings.timeout_seconds == None or retry_status.settings.timeout_seconds < 0:
            return True, 0
        if retry_status.settings.timeout_seconds == 0:
            return True, 0
        start_time_as_datetime = timeutil.utc_from_string(retry_status.start_time)
        duration_passed = now_as_datetime - start_time_as_datetime
        if duration_passed.total_seconds() > retry_status.settings.timeout_seconds:
            return True, duration_passed.total_seconds()
        else: 
            return False, None

    def __has_interval_passed(self, now_as_datetime, retry_status):
        if retry_status == None:
            return True, 0
        if retry_status.settings.interval_seconds == None or retry_status.settings.interval_seconds <= 0:
            return True, 0
        if retry_status.recent_attempt_times == None or len(retry_status.recent_attempt_times) == 0:
            return True, 0
        last_attempt_as_datetime = timeutil.utc_from_string(retry_status.recent_attempt_times[-1])
        duration_passed = now_as_datetime - last_attempt_as_datetime
        if duration_passed.total_seconds() > retry_status.settings.interval_seconds:
            return True, (duration_passed.total_seconds()-retry_status.settings.interval_seconds)
        else:
            return False, None

    def __has_exceeded_max_attempts(self, retry_status):
        if retry_status == None:
            return False
        if retry_status.settings.max_attempts == None or retry_status.settings.max_attempts < 0:
            return False
        if retry_status.settings.max_attempts == 0:
            return True
        if retry_status.attempts >= retry_status.settings.max_attempts:
            return True
        else:
            return False

    def __update_retry_status(self, attempt_time, process_strategy_job, requeue_request): 
        if process_strategy_job.retry_status == None or process_strategy_job.retry_status.current_task != requeue_request.task_name:
            process_strategy_job.retry_status = RetryStatus(requeue_request.task_name, requeue_request.settings)
            process_strategy_job.retry_status.current_task = requeue_request.task_name
            process_strategy_job.retry_status.attempts = 1
            process_strategy_job.retry_status.start_time = attempt_time
            process_strategy_job.retry_status.recent_attempt_times = []
        else:
            process_strategy_job.retry_status.settings = requeue_request.settings
            process_strategy_job.retry_status.attempts += 1
            process_strategy_job.retry_status.recent_attempt_times.append(attempt_time)
            if len(process_strategy_job.retry_status.recent_attempt_times) > 5:
                process_strategy_job.retry_status.recent_attempt_times.pop(0)
        logger.info(f'Retry status updated: {process_strategy_job.retry_status}')     

    def __clear_retry_status(self, process_strategy_job):
        process_strategy_job.retry_status = None
        logger.info(f'Retry status cleared')

    def __mark_as_running(self, report_status):
        if report_status.state != StrategyExecutionStates.RUNNING:
            report_status.state = StrategyExecutionStates.RUNNING
            self.kegd_persister.update(report_status.uid, report_status)

    def __check_retry_status(self, process_strategy_job):
        now_as_datetime = timeutil.get_utc_datetime()
        errors = []
        cancel_process = False
        requeue_process = False
        retry_status = process_strategy_job.retry_status
        if retry_status != None:
            timedout, duration = self.__has_retry_timedout(now_as_datetime, retry_status)
            if timedout:
                cancel_process = True
                errors.append(f'Retryable task {retry_status.current_task} has exceeded timeout of {retry_status.settings.timeout_seconds} seconds after {process_strategy_job.retry_status.attempts} attempts (started {duration} seconds ago)')
            else:
                interval_passed, _ = self.__has_interval_passed(now_as_datetime, retry_status)
                if not interval_passed:
                    # Requeue
                    requeue_process = True
        return cancel_process, errors, requeue_process

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
                        phase_result = self.__execute_output_extraction_task(report_status, keg_name, keg_status, strategy_execution, resource_context_properties)
                    elif report_status.phase == StrategyExecutionPhases.IMMEDIATE_CLEANUP or report_status.phase == StrategyExecutionPhases.IMMEDIATE_CLEANUP_ON_FAILURE:
                        phase_result = self.__process_immediate_cleanup(report_status, keg_name, keg_status, strategy_execution, all_errors)
                    elif report_status.phase == StrategyExecutionPhases.CLEANUP:
                        phase_result = self.__execute_cleanup(report_status, keg_name, keg_status, strategy_execution)
                except Exception as e:
                    logger.exception(f'An error occurred whilst processing phase \'{report_status.phase}\' of deployment strategy \'{report_status.uid}\' on group \'{keg_name}\'')
                    phase_result = PhaseResult(errors=[str(e)])

                if phase_result.requeue is not None:
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
            immediate_cleanup_num = NORMAL_PHASE_ORDER.index(StrategyExecutionPhases.IMMEDIATE_CLEANUP)
            phase_num = NORMAL_PHASE_ORDER.index(report_status.phase)
            if phase_num < immediate_cleanup_num:
                next_phase = StrategyExecutionPhases.IMMEDIATE_CLEANUP_ON_FAILURE
                # Update with errors so we don't lose them in case this request is dropped and picked up by another node
                if report_status.errors == None:
                    report_status.errors = []
                report_status.errors.extend(current_errors)
            else:
                next_phase = StrategyExecutionPhases.END
        else:
            phase_num = NORMAL_PHASE_ORDER.index(report_status.phase)
            next_phase_num = phase_num + 1
            if next_phase_num < len(NORMAL_PHASE_ORDER):
                next_phase = NORMAL_PHASE_ORDER[next_phase_num]
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
        requeue_request = None
        if strategy_execution.ready_check_task != None:
            ready_check_task = strategy_execution.ready_check_task
            handler = ReadyCheckHandler()
            ready_result = handler.handle(report_status.operation, keg_name, keg_status, self.context, ready_check_task, resource_context_properties)
            has_failed, reason = ready_result.has_failed()
            if has_failed:
                errors.append(reason)
            elif not ready_result.is_ready():
                requeue_request = RequeueRequest('Ready Check', ready_check_task.retry_settings)
        return PhaseResult(errors=errors, requeue=requeue_request)

    def __execute_output_extraction_task(self, report_status, keg_name, keg_status, strategy_execution, resource_context_properties):
        errors = []
        requeue_request = None
        if strategy_execution.output_extraction_task != None:
            output_extraction_task = strategy_execution.output_extraction_task
            handler = OutputExtractionHandler()
            extraction_result = handler.handle(report_status.operation, keg_name, keg_status, self.context, output_extraction_task, resource_context_properties)
            has_failed, reason = extraction_result.has_failed()
            if has_failed:
                errors.append(reason)
            else:
                report_status.outputs = extraction_result.outputs
        return PhaseResult(errors=errors)

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