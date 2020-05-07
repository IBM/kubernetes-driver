from .exceptions import InvalidDeploymentStrategyError

class WithdrawObjectAction:

    action_name = 'object'

    def __init__(self, group, kind, name, namespace=None):
        if group is None:
            raise InvalidDeploymentStrategyError(f'{WithdrawObjectAction.action_name} action missing \'group\' argument')
        if kind is None:
            raise InvalidDeploymentStrategyError(f'{WithdrawObjectAction.action_name} action missing \'kind\' argument')
        if name is None:
            raise InvalidDeploymentStrategyError(f'{WithdrawObjectAction.action_name} action missing \'name\' argument')
        self.group = group
        self.kind = kind
        self.name = name
        self.namespace = namespace

    @staticmethod
    def on_read(group=None, kind=None, name=None, namespace=None):
        return WithdrawObjectAction(group=group, kind=kind, name=name, namespace=namespace)

    def on_write(self):
        return {
            'group': self.group,
            'kind': self.kind,
            'name': self.name,
            'namespace': self.namespace
        }