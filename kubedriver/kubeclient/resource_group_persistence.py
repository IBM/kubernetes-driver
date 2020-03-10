import kubernetes.client as kubernetes_client_mod
from kubedriver.kuberesources.resource_config import ResourceConfiguration
from kubedriver.kubeclient.resource_group_record import ResourceGroupRecord, ResourceRecord

class ResourceConfigurationGroupPersistence:

    def persist_resource_group_record(self, resource_group_record):
        pass

    def get_resource_group_record(self, resource_group_record):
        pass


class ConfigMapResourceConfigurationGroupPersistence:

    def __init__(self, kube_client, resource_config_handler, resource_api_converter):
        self.kube_client = kube_client
        self.resource_config_handler = resource_config_handler

    def __determine_config_map_name(self, identifier):
        return 'KubedriverRecord{0}'.format(identifier)

    def __build_config_map_resource_config(self, resource_group_record):
        resource_records_data = []
        cm_name = self.__determine_config_map_name(resource_group_record.identifier)
        cm_config = {
            ResourceConfiguration.API_VERSION: 'v1',
            ResourceConfiguration.KIND: 'ConfigMap',
            ResourceConfiguration.METADATA: {
                ResourceConfiguration.NAME: cm_name
            },
            'data': {
                ResourceGroupRecord.IDENTIFIER: resource_group_record.identifier,
                ResourceGroupRecord.RESOURCE_RECORDS: resource_records_data
            }
        }
        for resource_record in resource_group_record.resource_records:
            resource_records_data.append({
                ResourceRecord.API_VERSION: resource_record.api_version,
                ResourceRecord.KIND: resource_record.kind,
                ResourceRecord.NAMESPACE: resource_record.namespace,
                ResourceRecord.NAME: resource_record.name
            })
        return ResourceConfiguration(cm_config)

    def persist_resource_group_record(self, resource_group_record):
        cm_config = self.__build_config_map_resource_config(resource_group_record)
        self.resource_config_handler.create_resource(cm_config)

    def get_resource_group_record(self, resource_group_record):
        cm_name = self.__determine_config_map_name(resource_group_record.identifier)
