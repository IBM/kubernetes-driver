
DEFAULT_OPERATION_CLEANUPS = {
    'Create': 'Delete',
    'Install': 'Uninstall',
    'Start': 'Stop'
}

DEFAULT_CLEANUP = 'Delete'

class DeploymentStrategy:

    def __init__(self, compose=None, cleanup_on=DEFAULT_CLEANUP):
        self.compose = compose if compose is not None else []
        self.cleanup_on = cleanup_on

    def get_compose_scripts_for(self, operation_name):
        compose_script = None
        need_cleanup = []
        for compose in self.compose:
            if compose.name == operation_name:
                compose_script = compose
            elif compose.cleanup_on == operation_name:
                need_cleanup.insert(0, compose)
            elif compose.cleanup_on == None and DEFAULT_OPERATION_CLEANUPS.get(compose.name) == operation_name:
                # Default cleanup in use if no cleanup has been set
                need_cleanup.insert(0, compose)
        return compose_script, need_cleanup
