import yaml
from .object_config import ObjectConfiguration
from .object_group import ObjectConfigurationGroup

class ObjectConfigurationDocument:

    def __init__(self, content):
        self.content = content
    
    def read(self):
        resource_docs = yaml.safe_load_all(self.content)
        object_configurations = []
        for resource_doc in resource_docs:
            if resource_doc != None: #empty doc
                object_configurations.append(ObjectConfiguration(resource_doc))
        return object_configurations
