import yaml
from .object_config import ObjectConfiguration
from .exceptions import InvalidObjectConfigurationDocumentError

class ObjectConfigurationDocument:

    def __init__(self, content):
        self.content = content
    
    def read(self):
        try:
            resource_docs = yaml.safe_load_all(self.content)
        except yaml.YAMLError as e:
            raise InvalidObjectConfigurationDocumentError(str(e), self.content) from e
        object_configurations = []
        for resource_doc in resource_docs:
            if resource_doc != None: #empty doc
                object_configurations.append(ObjectConfiguration(resource_doc))
        return object_configurations

    def read_raw(self):
        try:
            resource_docs = yaml.safe_load_all(self.content)
        except yaml.YAMLError as e:
            raise InvalidObjectConfigurationDocumentError(str(e), self.content) from e
        object_configurations = []
        for resource_doc in resource_docs:
            if resource_doc != None: #empty doc
                object_configurations.append(resource_doc)
        return object_configurations
