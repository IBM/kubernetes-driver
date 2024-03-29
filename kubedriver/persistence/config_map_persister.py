import logging
from kubernetes.client.rest import ApiException
from kubedriver.kubeobjects import ObjectConfiguration, ObjectAttributes
from .exceptions import RecordNotFoundError, PersistenceError, InvalidRecordError
from openshift.dynamic.exceptions import DynamicApiError, NotFoundError, BadRequestError

logger = logging.getLogger(__name__)

class ConfigMapPersister:

    def __init__(self, stored_type_name, kube_api_ctl, storage_namespace, record_builder, cm_api_version='v1', cm_kind='ConfigMap', cm_data_field='data'):
        self.stored_type_name = stored_type_name
        self.kube_api_ctl = kube_api_ctl
        self.storage_namespace = storage_namespace
        self.record_builder = record_builder
        self.cm_api_version = cm_api_version
        self.cm_kind = cm_kind
        self.cm_data_field = cm_data_field

    def __raise_error(self, operation, exception, config_map_name):
        if isinstance(exception, DynamicApiError):
            summary = exception.summary()
        else:
            summary = str(exception)
        message = f'Failed to {operation} record for {self.stored_type_name} \'{config_map_name}\' as an error occurred: {summary}'
        if isinstance(exception, NotFoundError):
            raise RecordNotFoundError(message) from exception
        elif isinstance(exception, BadRequestError):
            raise InvalidRecordError(message) from exception
        else:
            raise PersistenceError(message) from exception

    def build_record_reference(self, uid, record_name):
        return {
            'apiVersion': self.cm_api_version,
            'kind': self.cm_kind,
            'metadata': {
                'name': record_name,
                'namespace': self.storage_namespace,
                'uid': uid
            }
        }
    
    def get_record_uid(self, record_name, driver_request_id=None):
        record_cm = self.__get_config_map_for(record_name, driver_request_id=driver_request_id)
        return record_cm.metadata.uid
    
    def create(self, record_name, record_data, labels=None, driver_request_id=None):
        cm_config = self.__build_config_map_for_record(record_name, record_data, labels=labels)
        try:
            self.kube_api_ctl.create_object(cm_config, default_namespace=self.storage_namespace, driver_request_id=driver_request_id)
        except ApiException as e:
            self.__raise_error('create', e, record_name)

    def update(self, record_name, record_data, driver_request_id=None):
        existing_cm = self.__get_config_map_for(record_name, driver_request_id=driver_request_id)
        cm_config = self.__build_config_map_for_record(record_name, record_data, existing_cm=existing_cm)
        try:
            self.kube_api_ctl.update_object(cm_config, default_namespace=self.storage_namespace, driver_request_id=driver_request_id)
        except ApiException as e:
            self.__raise_error('update', e, record_name)

    def __get_config_map_for(self, record_name, driver_request_id=None):
        try:
            record_cm = self.kube_api_ctl.read_object(self.cm_api_version, self.cm_kind, record_name, namespace=self.storage_namespace, driver_request_id=driver_request_id)
            return record_cm
        except ApiException as e:
            self.__raise_error('read', e, record_name)

    def get(self, record_name, driver_request_id=None):
        record_cm = self.__get_config_map_for(record_name, driver_request_id=driver_request_id)
        return self.__read_config_map_to_record(record_cm)

    def delete(self, record_name, driver_request_id=None):
        try:
            self.kube_api_ctl.delete_object(self.cm_api_version, self.cm_kind, record_name, namespace=self.storage_namespace, driver_request_id=driver_request_id)
        except ApiException as e:
            self.__raise_error('delete', e, record_name)

    def __build_config_map_for_record(self, record_name, record_data, labels=None, existing_cm=None):
        if labels == None: 
            labels = {}
        if existing_cm is not None and existing_cm.metadata is not None and existing_cm.metadata.labels is not None:
            merged_labels = {}
            merged_labels.update(existing_cm.metadata.labels)
            merged_labels.update(labels)
            labels = merged_labels
        cm_obj_config = {
            ObjectAttributes.API_VERSION: self.cm_api_version,
            ObjectAttributes.KIND: self.cm_kind,
            ObjectAttributes.METADATA: {
                ObjectAttributes.NAME: record_name,
                ObjectAttributes.NAMESPACE: self.storage_namespace,
                ObjectAttributes.LABELS: labels
            },
            self.cm_data_field: {
                'record': self.record_builder.to_record(record_data)
            }
        }
        return ObjectConfiguration(cm_obj_config)

    def __read_config_map_to_record(self, config_map):
        cm_data = config_map.data
        record_data = cm_data.get('record')
        return self.record_builder.from_record(record_data)
