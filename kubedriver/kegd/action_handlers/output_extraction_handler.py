import logging
from kubedriver.kegd.model import OutputExtractionResult
from kubedriver.keg import CompositionReader
from kubedriver.sandbox import Sandbox, SandboxConfiguration, SandboxError, ExecuteError
from kubedriver.kegd.scripting import KegCollection, OutputExtractionResultHolder

logger = logging.getLogger(__name__)

#Different to regular task handlers

class OutputExtractionHandler:

    def handle(self, operation_name, keg_name, keg_status, location_context, output_extraction_task, resource_context_properties):
        script_file_name = output_extraction_task.script_file_name
        script = output_extraction_task.script
        sandbox = self.__build_sandbox()
        api_ctl = location_context.api_ctl
        objects = self.__load_composition(keg_status, api_ctl)
        result_holder = OutputExtractionResultHolder()
        inputs = self.__build_inputs(objects, result_holder, resource_context_properties)
        complete_script = self.__build_script(script)
        try:
            execute_result = sandbox.run(complete_script, file_name=script_file_name, inputs=inputs)
        except SandboxError as e:
            logger.exception(f'Error occurred during execution of output extraction script {script_file_name}: {str(e)}')
            full_detail = str(e)
            if isinstance(e, ExecuteError) and hasattr(e, 'log'):
                full_detail += '\n'
                full_detail += e.log.summarise()
            return OutputExtractionResult.failed(full_detail)

        log_msg = f'Output extraction script {script_file_name} complete, result: {result_holder}'
        if execute_result.log != None and execute_result.log.has_entries():
            log_msg += '\n'
            log_msg += execute_result.log.summarise()
        logger.info(log_msg)

        failed, reason = result_holder.has_failed()
        if failed:
            return OutputExtractionResult.failed(reason)
        else:
            #Make a copy of the outputs so they are clean (in case the holder has been contaminated)
            outputs = {}
            for k, v in result_holder.outputs.items():
                outputs[k] = str(v)
            return OutputExtractionResult.success(outputs)

    def __load_composition(self, keg_status, api_ctl):
        return CompositionReader().load_composition(keg_status, api_ctl)

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

    def __build_script(self, outputs_script):
        script = outputs_script
        script += '\ngetOutputs(keg, props, resultBuilder, log)'
        return script
            