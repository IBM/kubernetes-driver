from .exceptions import InvalidObjectConfigurationError
from .object_reference import ObjectReference
from .object_attrs import ObjectAttributes

class ObjectConfiguration:
    
    def __init__(self, data):
        self.data = data
        self.parse_resource_fields()

    def __validate_field_present(self, field_name):
        if field_name not in self.data:
            raise InvalidObjectConfigurationError(f'Missing \'{field_name}\' field', self.data)

    def __validate_subfield_present(self, parent_field_name, field_name):
        self.__validate_field_present(parent_field_name)
        data_part = self.data.get(parent_field_name)
        if field_name not in data_part:
            raise InvalidObjectConfigurationError(f'Missing \'{field_name}\' field in \'{parent_field_name}\'', self.data)

    def parse_resource_fields(self):
        self.__validate_field_present(ObjectAttributes.API_VERSION)
        self.__validate_field_present(ObjectAttributes.KIND)
        self.__validate_subfield_present(ObjectAttributes.METADATA, ObjectAttributes.NAME)
        self.api_version = self.data.get(ObjectAttributes.API_VERSION)
        self.kind = self.data.get(ObjectAttributes.KIND)
        self.metadata = self.data.get(ObjectAttributes.METADATA)
        self.name = self.metadata.get(ObjectAttributes.NAME)
        self.namespace = self.metadata.get(ObjectAttributes.NAMESPACE)

    @property
    def reference(self):
        return ObjectReference(self.api_version, self.kind, self.name, namespace=self.namespace)

    def __str__(self):
        return f'{self.__class__.__name__}({self.data})'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.data!r})'
        