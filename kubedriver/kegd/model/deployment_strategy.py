
DEFAULT_REVERSES = {
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
        reverses = []
        for compose in self.compose:
            if compose.name == operation_name:
                compose_script = compose
            elif compose.reverse == operation_name:
                reverses.insert(0, compose)
            elif compose.reverse == None and DEFAULT_REVERSES.get(compose.name) == operation_name:
                # Default reverse in use if no reverse has been set
                reverses.insert(0, compose)
        return compose_script, reverses
