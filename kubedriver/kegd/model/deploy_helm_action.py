from .exceptions import InvalidDeploymentStrategyError

class DeployHelmAction:

    action_name = 'helm'

    def __init__(self, chart, name, namespace=None, values=None):
        if chart is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'chart\' argument')
        if name is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'name\' argument')
        self.chart = chart
        self.name = name
        self.namespace = namespace
        self.values = values

    @staticmethod
    def on_read(chart=None, name=None, namespace=None, values=None):
        return DeployHelmAction(chart, name, namespace=namespace, values=values)

    def on_write(self):
        return {
            'chart': self.chart,
            'name': self.name,
            'values': self.values,
            'namespace': self.namespace
        }