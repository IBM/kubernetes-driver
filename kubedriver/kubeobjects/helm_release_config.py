class HelmReleaseConfiguration:

    CHART = 'chart'
    NAME = 'name'
    NAMESPACE = 'namespace'
    VALUES = 'values'

    def __init__(self, chart, name, namespace, values):
        self.chart = chart
        self.name = name
        self.namespace = namespace
        self.values = values

    def __str__(self):
        return f'{self.__class__.__name__}(chart: {self.chart}, name: {self.name}, namespace: {self.namespace}, values: {self.values})'

    def __repr__(self):
        return f'{self.__class__.__name__}(chart: {self.chart!r}, name: {self.name!r}, namespace: {self.namespace!r}, values: {self.values!r})'
