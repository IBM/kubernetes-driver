from .exceptions import InvalidObjectConfigurationError

class ObjectConfiguration:

    API_VERSION = 'apiVersion'
    KIND = 'kind'
    METADATA = 'metadata'
    NAME = 'name'
    NAMESPACE = 'namespace'

    def __init__(self, conf):
        self.conf = conf
        self.__parse_resource_fields()

    def __validate_field_present(self, field_name):
        if field_name not in self.conf:
            raise InvalidObjectConfigurationError('Missing \'{0}\' field'.format(field_name), self.conf)

    def __validate_subfield_present(self, parent_field_name, field_name):
        self.__validate_field_present(parent_field_name)
        data_part = self.conf.get(parent_field_name)
        if field_name not in data_part:
            raise InvalidObjectConfigurationError('Missing \'{0}\' field in \'{1}\''.format(field_name, parent_field_name), self.conf)

    def __parse_resource_fields(self):
        self.__validate_field_present(self.API_VERSION)
        self.__validate_field_present(self.KIND)
        self.__validate_subfield_present(self.METADATA, self.NAME)
        self.api_version = self.conf.get(self.API_VERSION)
        self.kind = self.conf.get(self.KIND)
        self.metadata = self.conf.get(self.METADATA)
        self.name = self.metadata.get(self.NAME)
        self.namespace = self.metadata.get(self.NAMESPACE, None)

    def __str__(self):
        return f'{self.__class__.__name__}({self.conf})'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.conf!r})'
        