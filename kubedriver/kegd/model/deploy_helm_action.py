from .exceptions import InvalidDeploymentStrategyError

class DeployHelmAction:

    action_name = 'helm'

    def __init__(self, chart, name, namespace=None, values=None, chart_encoded=False, tags=None):
        if chart is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'chart\' argument')
        if name is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'name\' argument')
        self.chart = chart
        self.name = name
        self.namespace = namespace
        self.values = values
        self.chart_encoded = chart_encoded
        self.tags = tags

    @staticmethod
    def on_read(chart=None, name=None, namespace=None, values=None, chartEncoded=False, tags=None):
        return DeployHelmAction(chart, name, namespace=namespace, values=values, chart_encoded=chartEncoded, tags=tags)

    def on_write(self):
        return {
            'chart': self.chart,
            'name': self.name,
            'values': self.values,
            'namespace': self.namespace,
            'chartEncoded': self.chart_encoded
        }