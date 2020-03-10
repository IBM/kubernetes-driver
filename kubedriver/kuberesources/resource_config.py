from .exceptions import InvalidResourceConfigurationError

class ResourceConfiguration:

    API_VERSION = 'apiVersion'
    KIND = 'kind'
    METADATA = 'metadata'
    NAME = 'name'

    def __init__(self, resource_data):
        self.resource_data = resource_data
        self.__parse_resource_fields()

    def __validate_field_present(self, field_name):
        if field_name not in self.resource_data:
            raise InvalidResourceConfigurationError('Missing \'{0}\' field'.format(field_name), self.resource_data)

    def __validate_subfield_present(self, parent_field_name, field_name):
        self.__validate_field_present(parent_field_name)
        data_part = self.resource_data.get(parent_field_name)
        if field_name not in data_part:
            raise InvalidResourceConfigurationError('Missing \'{0}\' field in \'{1}\''.format(field_name, parent_field_name), self.resource_data)

    def __parse_resource_fields(self):
        self.__validate_field_present(self.API_VERSION)
        self.__validate_field_present(self.KIND)
        self.__validate_subfield_present(self.METADATA, self.NAME)
        self.api_version = self.resource_data.get(self.API_VERSION)
        self.kind = self.resource_data.get(self.KIND)
        self.metadata = self.resource_data.get(self.METADATA)
        self.name = self.metadata.get(self.NAME)
