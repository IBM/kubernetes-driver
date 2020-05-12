
class SandboxError(Exception):
    pass

class CompileError(SandboxError):
    pass


class ExecuteError(SandboxError):
    pass