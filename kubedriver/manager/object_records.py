

class DeployedObjectGroupRecord:

    IDENTIFIER = 'identifier'
    OBJECT_RECORDS = 'objectRecords'

    def __init__(self, identifier, object_records):
        self.identifier = identifier
        self.object_records = object_records

    def __str__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier}, object_records: {self.object_records})'

    def __repr__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier!r}, object_records: {self.object_records!r})'

class DeployedObjectRecord:

    API_VERSION = 'apiVersion'
    KIND = 'kind'
    NAMESPACE = 'namespace'
    NAME = 'name'

    def __init__(self, api_version, kind, namespace, name):
        self.api_version = api_version
        self.kind = kind
        self.namespace = namespace
        self.name = name

    @staticmethod
    def from_dict(data):
        api_version = data.get(DeployedObjectRecord.API_VERSION)
        kind = data.get(DeployedObjectRecord.KIND)
        namespace = data.get(DeployedObjectRecord.NAMESPACE, None)
        name = data.get(DeployedObjectRecord.NAME)
        return DeployedObjectRecord(api_version, kind, namespace, name)

    def __str__(self):
        return f'{self.__class__.__name__}(api_version: {self.api_version}, kind: {self.kind}, namespace: {self.namespace}, name: {self.name})'

    def __repr__(self):
        return f'{self.__class__.__name__}(api_version: {self.api_version!r}, kind: {self.kind!r}, namespace: {self.namespace!r}, name: {self.name!r})'
