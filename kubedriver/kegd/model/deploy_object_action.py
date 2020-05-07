from .exceptions import InvalidDeploymentStrategyError

class DeployObjectAction:

    action_name = 'object'

    def __init__(self, group, kind, name, config, namespace=None, tags=None):
        if group is None:
            raise InvalidDeploymentStrategyError(f'{DeployObjectAction.action_name} action missing \'group\' argument')
        if kind is None:
            raise InvalidDeploymentStrategyError(f'{DeployObjectAction.action_name} action missing \'kind\' argument')
        if name is None:
            raise InvalidDeploymentStrategyError(f'{DeployObjectAction.action_name} action missing \'name\' argument')
        if config is None:
            raise InvalidDeploymentStrategyError(f'{DeployObjectAction.action_name} action missing \'config\' argument')
        self.group = group
        self.kind = kind
        self.name = name
        self.config = config
        self.namespace = namespace
        self.tags = tags

    @staticmethod
    def on_read(group=None, kind=None, name=None, config=None, namespace=None, tags=None):
        return DeployObjectAction(group=group, kind=kind, name=name, config=config, namespace=namespace, tags=tags)

    def on_write(self):
        return {
            'group': self.group,
            'kind': self.kind,
            'name': self.name,
            'config': self.config,
            'namespace': self.namespace,
            'tags': self.tags
        }