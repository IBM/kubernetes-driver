from .exceptions import InvalidDeploymentStrategyError

class DeployHelmAction:

    action_name = 'helm'

    def __init__(self, chart, name, namespace=None, values=None, setfiles=None,
                 chart_encoded=False, tags=None, wait=None, timeout=None):
        if chart is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'chart\' argument')
        if name is None:
            raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} action missing \'name\' argument')
        self.chart = chart
        self.name = name
        self.namespace = namespace

        if values is not None:
            if isinstance(values, str):
                # Multiple value files are to be passed as a list of strings
                # Keep this check for backwards compatibility with older assemblies.
                self.values = [values]
            elif not isinstance(values, list):
                raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} expected values to be a list of strings, found '+str(isinstance(values))+' instead')
            else:
                self.values = values
        else:
            self.values = None

        if setfiles is not None:
            if not isinstance(setfiles, dict):
                raise InvalidDeploymentStrategyError(f'{DeployHelmAction.action_name} expected setfiles to be a dict <key>:<value-file>, found '+str(isinstance(values))+' instead')
            else:
                self.setfiles = setfiles
        else:
            self.setfiles = None

        self.chart_encoded = chart_encoded
        self.tags = tags
        self.wait = wait
        self.timeout = timeout

    @staticmethod
    def on_read(chart=None, name=None, namespace=None, values=None, setfiles=None,
                chartEncoded=False, tags=None, wait=None, timeout=None):
        return DeployHelmAction(chart, name, namespace=namespace, values=values, setfiles=setfiles,
               chart_encoded=chartEncoded, tags=tags, wait=wait, timeout=timeout)

    def on_write(self):
        return {
            'chart': self.chart,
            'name': self.name,
            'values': self.values,
            'setfiles': self.setfiles,
            'namespace': self.namespace,
            'chartEncoded': self.chart_encoded,
            'wait': self.wait,
            'timeout': self.timeout
        }