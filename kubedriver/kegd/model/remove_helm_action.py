from .exceptions import InvalidDeploymentStrategyError

class RemoveHelmAction:

    action_name = 'helm'

    def __init__(self, name, namespace=None):
        if name is None:
            raise InvalidDeploymentStrategyError(f'{RemoveHelmAction.action_name} action missing \'name\' argument')
        self.name = name
        self.namespace = namespace

    @staticmethod
    def on_read(name=None, namespace=None):
        return RemoveHelmAction(name, namespace=namespace)

    def on_write(self):
        return {
            'name': self.name,
            'namespace': self.namespace
        }