import yaml
import re
from kubernetes.client.rest import ApiException
from kubedriver.kubeclient import ErrorReader
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeobjects import namehelper
from .records import EntityGroupRecord, ObjectRecord, RequestRecord, HelmReleaseRecord
from .exceptions import PersistenceError, InvalidUpdateError, RecordNotFoundError

class ConfigMapStorageFormat:

    def dump_group_record(self, group_record):
        dump = {
            EntityGroupRecord.UID: group_record.uid,
            EntityGroupRecord.REQUESTS: self.dump_request_records(group_record.requests)
        }
        if len(group_record.objects) > 0:
            dump[EntityGroupRecord.OBJECTS] = self.dump_object_records(group_record.objects)
        if len(group_record.helm_releases) > 0:
            dump[EntityGroupRecord.HELM_RELEASES] = self.dump_helm_records(group_record.helm_releases)
        return dump

    def load_group_record(self, data):
        uid = data.get(EntityGroupRecord.UID)
        raw_objects = data.get(EntityGroupRecord.OBJECTS)
        objects = self.load_object_records(raw_objects)
        raw_requests = data.get(EntityGroupRecord.REQUESTS)
        requests = self.load_request_records(raw_requests)
        raw_helm_releases = data.get(EntityGroupRecord.HELM_RELEASES)
        helm_releases = self.load_helm_records(raw_helm_releases)
        return EntityGroupRecord(uid, objects, helm_releases=helm_releases, requests=requests)

    def dump_request_record(self, request_record):
        dump = {
            RequestRecord.UID: request_record.uid,
            RequestRecord.OPERATION: request_record.operation,
            RequestRecord.STATE: request_record.state,
            RequestRecord.ERROR: request_record.error
        }
        return dump

    def load_request_record(self, data):
        uid = data.get(RequestRecord.UID)
        operation = data.get(RequestRecord.OPERATION)
        state = data.get(RequestRecord.STATE)
        error = data.get(RequestRecord.ERROR)
        return RequestRecord(uid, operation, state=state, error=error)

    def dump_request_records(self, request_records):
        pre_dump = []
        if request_records != None:
            for request in request_records:
                pre_dump.append(self.dump_request_record(request))
        return yaml.safe_dump(pre_dump)

    def load_request_records(self, data):
        if data == None:
            return []
        raw_records = yaml.safe_load(data)
        records = []
        for raw_record in raw_records:
            records.append(self.load_request_record(raw_record))
        return records

    def dump_helm_record(self, helm_record):
        dump = {
            HelmReleaseRecord.CHART: helm_record.chart,
            HelmReleaseRecord.NAME: helm_record.name,
            HelmReleaseRecord.NAMESPACE: helm_record.namespace,
            HelmReleaseRecord.VALUES: helm_record.values
        }
        return dump

    def load_helm_record(self, data):
        chart = data.get(HelmReleaseRecord.CHART)
        name = data.get(HelmReleaseRecord.NAME)
        namespace = data.get(HelmReleaseRecord.NAMESPACE)
        values = data.get(HelmReleaseRecord.VALUES)
        return HelmReleaseRecord(chart, name, namespace, values)
    
    def dump_helm_records(self, helm_records):
        pre_dump = []
        if helm_records != None:
            for record in helm_records:
                pre_dump.append(self.dump_helm_record(record))
        return yaml.safe_dump(pre_dump)
    
    def load_helm_records(self, data):
        if data == None:
            return []
        raw_records = yaml.safe_load(data)
        helm_records = []
        for raw_record in raw_records:
            helm_records.append(self.load_helm_record(raw_record))
        return helm_records

    def dump_object_record(self, object_record):
        dump = {
            ObjectRecord.CONFIG: object_record.config,
            ObjectRecord.STATE: object_record.state,
            ObjectRecord.ERROR: object_record.error
        }
        return dump

    def load_object_record(self, data):
        config = data.get(ObjectRecord.CONFIG)
        state = data.get(ObjectRecord.STATE)
        error = data.get(ObjectRecord.ERROR)
        return ObjectRecord(config, state=state, error=error)

    def dump_object_records(self, object_records):
        pre_dump = []
        if object_records != None:
            for record in object_records:
                pre_dump.append(self.dump_object_record(record))
        return yaml.safe_dump(pre_dump)
    
    def load_object_records(self, data):
        if data == None:
            return []
        raw_objs = yaml.safe_load(data)
        objects = []
        for raw_obj in raw_objs:
            objects.append(self.load_object_record(raw_obj))
        return objects

class ConfigMapRecordPersistence:

    def __init__(self, kube_api_ctl, storage_namespace, cm_api_version='v1', cm_kind='ConfigMap', cm_data_field='data', error_reader=None):
        self.kube_api_ctl = kube_api_ctl
        self.storage_namespace = storage_namespace
        self.cm_api_version = cm_api_version
        self.cm_kind = cm_kind
        self.cm_data_field = cm_data_field
        self.format = ConfigMapStorageFormat()
        self.error_reader = error_reader if error_reader is not None else ErrorReader()

    def __raise_error(self, operation, exception, record_uid):
        message = f'Failed to {operation} record for Group \'{record_uid}\' as an error occurred: {self.error_reader.summarise_error(exception)}'
        if self.error_reader.is_not_found_err(exception):
            raise RecordNotFoundError(message) from exception
        elif self.error_reader.is_client_error(exception):
            raise InvalidUpdateError(message) from exception
        else:
            raise PersistenceError(message) from exception

    def create(self, group_record):
        cm_config = self.__build_config_map_for_record(group_record)
        try:
            self.kube_api_ctl.create_object(cm_config, default_namespace=self.storage_namespace)
        except ApiException as e:
            self.__raise_error('create', e, group_record.uid)

    def update(self, group_record):
        cm_config = self.__build_config_map_for_record(group_record)
        try:
            self.kube_api_ctl.update_object(cm_config, default_namespace=self.storage_namespace)
        except ApiException as e:
            self.__raise_error('update', e, group_record.uid)

    def get(self, group_uid):
        cm_name = self.__determine_config_map_name(group_uid)
        try:
            record_cm = self.kube_api_ctl.read_object(self.cm_api_version, self.cm_kind, cm_name, namespace=self.storage_namespace)
        except ApiException as e:
            self.__raise_error('read', e, group_uid)
        else:
            return self.__read_config_map_to_record(record_cm)

    def delete(self, group_uid):
        cm_name = self.__determine_config_map_name(group_uid)
        try:
            self.kube_api_ctl.delete_object(self.cm_api_version, self.cm_kind, cm_name, namespace=self.storage_namespace)
        except ApiException as e:
            self.__raise_error('delete', e, group_uid)

    def __determine_config_map_name(self, group_uid):
        potential_name = 'keg-{0}'.format(group_uid)
        valid, reason = namehelper.is_valid_subdomain_name(potential_name)
        if not valid: 
            raise PersistenceError(f'Could not generate valid ConfigMap name for Group \'{potential_name}\': {str(reason)}')
        return potential_name

    def __build_config_map_for_record(self, group_record):
        cm_name = self.__determine_config_map_name(group_record.uid)
        cm_obj_config = {
            ObjectConfiguration.API_VERSION: self.cm_api_version,
            ObjectConfiguration.KIND: self.cm_kind,
            ObjectConfiguration.METADATA: {
                ObjectConfiguration.NAME: cm_name,
                ObjectConfiguration.NAMESPACE: self.storage_namespace
            },
            self.cm_data_field: self.format.dump_group_record(group_record)
        }
        return ObjectConfiguration(cm_obj_config)

    def __read_config_map_to_record(self, config_map):
        cm_data = config_map.data
        group_record = self.format.load_group_record(cm_data)
        return group_record
