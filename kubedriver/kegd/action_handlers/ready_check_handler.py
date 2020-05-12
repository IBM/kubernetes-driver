import logging
from kubedriver.kegd.model import ReadyResult
from kubedriver.utils.to_dict import to_dict
from kubedriver.sandbox import Sandbox, SandboxConfiguration, SandboxError, ExecuteError
from kubedriver.kegd.scripting import KegCollection, ReadyResultHolder

logger = logging.getLogger(__name__)

#Different to regular task handlers

class ReadyCheckHandler:

    def handle(self, operation_name, keg_name, keg_status, location_context, ready_check_task, resource_context_properties):
        ready_script_file_name = ready_check_task.script_file_name
        ready_script = ready_check_task.script
        sandbox = self.__build_sandbox()
        api_ctl = location_context.api_ctl
        objects = self.__load_composition(keg_status, api_ctl)
        result_holder = ReadyResultHolder()
        inputs = self.__build_inputs(objects, result_holder, resource_context_properties)
        complete_script = self.__build_script(ready_script)
        try:
            execute_result = sandbox.run(complete_script, file_name=ready_script_file_name, inputs=inputs)
        except SandboxError as e:
            logger.exception(f'Error occured during execution of readiness script {ready_script_file_name}: {str(e)}')
            full_detail = str(e)
            if isinstance(e, ExecuteError) and hasattr(e, 'log'):
                full_detail += '\nExecution Log:'
                for entry in e.log.get_entries():
                    full_detail += f'\n{entry}'
            error_msg = str(e)
            return ReadyResult.failed(error_msg)

       
        log_msg = f'Ready script {ready_script_file_name} complete, result: {result_holder}'
        if execute_result.log != None:
            log_entries = execute_result.log.get_entries()
            if len(log_entries) > 0:
                log_msg += ', log:'
                for entry in log_entries:
                    log_msg += f'\n{entry}'
        logger.info(log_msg)

        if result_holder.is_ready():
            return ReadyResult.ready()
        else:
            failed, reason = result_holder.has_failed()
            if failed:
                return ReadyResult.failed(reason)
        return ReadyResult.not_ready()

    def __load_composition(self, keg_status, api_ctl):
        objects = []
        if keg_status.composition != None:
            if keg_status.composition.objects != None:
                for object_status in keg_status.composition.objects:
                    found, obj = api_ctl.safe_read_object(object_status.group, object_status.kind, object_status.name, namespace=object_status.namespace)
                    if found:
                        if api_ctl.is_object_custom(object_status.group, object_status.kind):
                            objects.append(obj)
                        else:
                            objects.append(to_dict(obj)) 
        return objects

    def __build_sandbox(self):
        config = SandboxConfiguration()
        config.include_log = True
        config.log_member_name = 'log'
        return Sandbox(config)

    def __build_inputs(self, objects, result_holder, resource_context_properties):
        inputs = {}
        inputs['keg'] = KegCollection(objects)
        inputs['resultBuilder'] = result_holder
        inputs['props'] = resource_context_properties
        return inputs

    def __build_script(self, ready_script):
        script = ready_script
        script += '\ncheck_ready(keg, props, resultBuilder, log)'
        return script
            