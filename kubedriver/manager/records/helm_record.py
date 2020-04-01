from .object_states import ObjectStates

class HelmRecord:

    CHART = 'chart'
    NAME = 'name'
    NAMESPACE = 'namespace'
    VALUES = 'values'
    STATE = 'state'
    ERROR = 'error'

    def __init__(self, chart, name, namespace, values, state=ObjectStates.PENDING, error=None):
        self.chart = chart
        self.name = name
        self.namespace = namespace
        self.values = values
        self.state = state
        self.error = error

    def __str__(self):
        return f'{self.__class__.__name__}(chart: {self.chart}, name: {self.name}, namespace: {self.namespace}, values: {self.values}, state: {self.state}, error: {self.error})'

    def __repr__(self):
        return f'{self.__class__.__name__}(chart: {self.chart!r}, name: {self.name!r}, namespace: {self.namespace!r}, values: {self.values!r}, state: {self.state!r}, error: {self.error!r})'
