import yaml
import re
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeobjects import namehelper
from .object_records import DeployedObjectGroupRecord, DeployedObjectRecord

class ConfigMapRecordPersistence:

    def __init__(self, kube_api_ctl, storage_namespace, cm_api_version='v1', cm_kind='ConfigMap', cm_data_field='data'):
        self.kube_api_ctl = kube_api_ctl
        self.storage_namespace = storage_namespace
        self.cm_api_version = cm_api_version
        self.cm_kind = cm_kind
        self.cm_data_field = cm_data_field

    def __determine_config_map_name(self, identifier):
        potential_name = 'kdr-{0}'.format(identifier)
        return namehelper.safe_subdomain_name(potential_name)

    def __build_config_map_for_record(self, object_group_record):
        object_records_cm_list = []
        for object_record in object_group_record.object_records:
            object_records_cm_list.append({
                DeployedObjectRecord.API_VERSION: object_record.api_version,
                DeployedObjectRecord.KIND: object_record.kind,
                DeployedObjectRecord.NAMESPACE: object_record.namespace,
                DeployedObjectRecord.NAME: object_record.name
            })
        object_records_str = yaml.safe_dump(object_records_cm_list)
        cm_name = self.__determine_config_map_name(object_group_record.identifier)
        cm_obj_config = {
            ObjectConfiguration.API_VERSION: self.cm_api_version,
            ObjectConfiguration.KIND: self.cm_kind,
            ObjectConfiguration.METADATA: {
                ObjectConfiguration.NAME: cm_name,
                ObjectConfiguration.NAMESPACE: self.storage_namespace
            },
            self.cm_data_field: {
                DeployedObjectGroupRecord.IDENTIFIER: object_group_record.identifier,
                DeployedObjectGroupRecord.OBJECT_RECORDS: object_records_str
            }
        }
        return ObjectConfiguration(cm_obj_config)

    def persist_object_group_record(self, object_group_record):
        cm_config = self.__build_config_map_for_record(object_group_record)
        self.kube_api_ctl.create_object(cm_config, default_namespace=self.storage_namespace)

    def get_object_group_record(self, object_group_identifier):
        cm_name = self.__determine_config_map_name(object_group_identifier)
        record_cm = self.kube_api_ctl.read_object(self.cm_api_version, self.cm_kind, cm_name, namespace=self.storage_namespace)
        return self.__convert_into_object_group_record(record_cm)

    def delete_object_group_record(self, object_group_identifier):
        cm_name = self.__determine_config_map_name(object_group_identifier)
        self.kube_api_ctl.delete_object(self.cm_api_version, self.cm_kind, cm_name, namespace=self.storage_namespace)

    def __convert_into_object_group_record(self, record_cm):
        cm_data = record_cm.data
        group_identifier = cm_data.get(DeployedObjectGroupRecord.IDENTIFIER)
        object_records_cm_str = cm_data.get(DeployedObjectGroupRecord.OBJECT_RECORDS)
        object_records_cm_list = yaml.safe_load(object_records_cm_str)
        object_records = []
        for object_record_cm_data in object_records_cm_list:
            object_records.append(DeployedObjectRecord.from_dict(object_record_cm_data))
        return DeployedObjectGroupRecord(group_identifier, object_records)