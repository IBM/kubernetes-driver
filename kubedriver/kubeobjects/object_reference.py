from .exceptions import InvalidObjectConfigurationError

class ObjectReference:
    
    API_VERSION = 'apiVersion'
    KIND = 'kind'
    METADATA = 'metadata'
    NAME = 'name'
    NAMESPACE = 'namespace'

    def __init__(self, api_version, kind, name, namespace=None):
        self.api_version = api_version
        self.kind = kind
        self.name = name
        self.namespace = namespace

    def __str__(self):
        return f'{self.__class__.__name__}(api_version: {self.api_version}, kind: {self.kind}, name: {self.name}, namespace: {self.namespace})'

    def __repr__(self):
        return f'{self.__class__.__name__}(api_version: {self.api_version!r}, kind: {self.kind!r}, name: {self.name!r}, namespace: {self.namespace!r})'

    