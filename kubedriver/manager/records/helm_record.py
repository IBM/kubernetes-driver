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

    @staticmethod
    def from_storage_data(self, data):
        chart = data.get(HelmRecord.CHART)
        name = data.get(HelmRecord.NAME)
        namespace = data.get(HelmRecord.NAMESPACE)
        values = data.get(HelmRecord.VALUES)
        state = data.get(HelmRecord.STATE, ObjectStates.PENDING)
        error = data.get(HelmRecord.ERROR, None)
        return HelmRecord(chart, name, namespace, values, state=state, error=error)

    def to_storage_data(self):
        data = {
            HelmRecord.CHART: self.chart,
            HelmRecord.NAME: self.name,
            HelmRecord.NAMESPACE: self.namespace, 
            HelmRecord.VALUES: self.values,
            ObjectRecord.STATE: self.state,
            ObjectRecord.ERROR: self.error
        }
        return data

    def __str__(self):
        return f'{self.__class__.__name__}(chart: {self.chart}, name: {self.name}, namespace: {self.namespace}, values: {self.values}, state: {self.state}, error: {self.error})'

    def __repr__(self):
        return f'{self.__class__.__name__}(chart: {self.chart!r}, name: {self.name!r}, namespace: {self.namespace!r}, values: {self.values!r}, state: {self.state!r}, error: {self.error!r})'
