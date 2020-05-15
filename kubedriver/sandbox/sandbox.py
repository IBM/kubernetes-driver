import logging
from RestrictedPython import compile_restricted_exec, safe_builtins
from RestrictedPython.Guards import guarded_unpack_sequence
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.PrintCollector import PrintCollector
from .exceptions import CompileError, ExecuteError
from .execution import ExecutionResult
from .config import SandboxConfiguration
from .log import Log

logger = logging.getLogger(__name__)

def safer_getitem(obj, name, default=None, getattr=getattr):
    if type(obj) == dict:
        if type(name) == str:
            if name.startswith('_'):
                raise AttributeError(f'"{name}" is an invalid attribute name because it starts with "_"')
        elif type(name) != int:
            raise AttributeError(f'dict keys must be integers or str, not {type(name)}')
    elif type(obj) == list:
        if type(name) != int and type(name) != slice:
            raise AttributeError(f'list indices must be integers or slices, not {type(name)}')
    return obj[name]

class Sandbox:

    def __init__(self, configuration):
        if configuration == None:
            configuration = SandboxConfiguration()
        self._log = None
        self._log_member_name = 'log'
        if configuration.include_log:
            self._log = Log()
        if configuration.log_member_name is not None:
            self._log_member_name = configuration.log_member_name

    def run(self, script, file_name='<inline code>', inputs=None):
        compile_result = compile_restricted_exec(script, filename=file_name)
        if compile_result.errors != None and len(compile_result.errors) > 0:
            raise CompileError(f'Compilation of {file_name} failed with errors: {compile_result.errors}')
        if inputs == None:
            inputs = {}
        builtins = self.__build_builtins()
        global_scope = {'__builtins__': builtins}
        local_scope = {}
        self.__add_inputs(local_scope, inputs)
        self.__add_configured_utilities(local_scope)
        try:
            exec(compile_result.code, global_scope, local_scope)
        except Exception as e:
            raise ExecuteError(f'Sandbox execution of script {file_name} returned an error: {e}', execution_log=self._log) from e
        return ExecutionResult(global_scope, local_scope, log=self._log)

    def __build_builtins(self):
        builtins = safe_builtins.copy()
        builtins['_unpack_sequence_'] = guarded_unpack_sequence
        builtins['_getiter_'] = default_guarded_getiter
        builtins['_getitem_'] = safer_getitem
        return builtins

    def __add_configured_utilities(self, local_scope):
        if self._log is not None:
            local_scope[self._log_member_name] = self._log

    def __add_inputs(self, local_scope, inputs):
        for k, v in inputs.items():
            local_scope[k] = v