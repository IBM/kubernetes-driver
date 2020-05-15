
class SandboxError(Exception):
    pass

class CompileError(SandboxError):
    pass


class ExecuteError(SandboxError):
    
    def __init__(self, *args, **kwargs):
        if 'execution_log' in kwargs:
            self.execution_log = kwargs.pop('execution_log')
        super().__init__(*args, **kwargs)