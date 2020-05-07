from .exceptions import InvalidDeploymentStrategyError

class DeployObjectsAction:

    action_name = 'objects'

    def __init__(self, file, **kwargs):
        super().__init__(**kwargs)
        if file is None:
            raise InvalidDeploymentStrategyError(f'{DeployObjectsAction.action_name} action missing \'file\' argument')
        self.file = file
        
    @staticmethod
    def on_read(file=None):
        return DeployObjectsAction(file)

    def on_write(self):
        return {
            'file': self.file
        }