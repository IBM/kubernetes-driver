class DeploymentStrategy:
    
    def __init__(self, compose=None):
        self.compose = compose if compose is not None else []

    def get_compose_scripts_for(self, operation_name):
        compose_script = None
        reverses = []
        for compose in self.compose:
            if compose.name == operation_name:
                compose_script = compose
            elif compose.reverse == operation_name:
                reverses.insert(0, compose)
        return compose_script, reverses
