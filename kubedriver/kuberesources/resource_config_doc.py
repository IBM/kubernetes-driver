import yaml
from .resource_config import ResourceConfiguration
from .resource_config_group import ResourceConfigurationGroup

class ResourceConfigurationDocuments:

    def __init__(self, content):
        self.content = content
    
    def read(self):
        resource_docs = yaml.safe_load_all(self.content)
        resource_configurations = []
        for resource_doc in resource_docs:
            if resource_doc != None: #empty doc
                resource_configurations.append(ResourceConfiguration(resource_doc))
        return resource_configurations
