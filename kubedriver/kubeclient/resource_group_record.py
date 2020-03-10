

class ResourceGroupRecord:

    IDENTIFIER = 'identifier'
    RESOURCE_RECORDS = 'resourceRecords'

    def __init__(self, identifier, resource_records):
        self.identifier = identifier
        self.resource_records = resource_records

class ResourceRecord:

    API_VERSION = 'apiVersion'
    KIND = 'kind'
    NAMESPACE = 'namespace'
    NAME = 'name'

    def __init__(self, api_version, kind, namespace, name):
        self.api_version = api_version
        self.kind = kind
        self.namespace = namespace
        self.name = name