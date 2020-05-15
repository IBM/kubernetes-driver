

class ExecutionResult:

    def __init__(self, global_scope, local_scope, log=None):
        self.global_scope = global_scope
        self.local_scope = local_scope
        self.log = log