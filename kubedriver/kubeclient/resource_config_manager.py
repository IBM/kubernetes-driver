

class ResourceConfigurationManager:

    def __init__(self, resource_config_handler, resource_persistence=None):
        self.resource_config_handler = resource_config_handler
        self.resource_group_persistence = resource_group_persistence

    def create_resource_group(self, kube_client, resource_config_group):
        pass
