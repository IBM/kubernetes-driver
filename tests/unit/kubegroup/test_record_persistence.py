import unittest
import yaml
import json
import tests.matchers as matchers
import tests.utils as testutils
from unittest.mock import MagicMock
from kubernetes.client import V1ConfigMap
from kubernetes.client.rest import ApiException
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubegroup.exceptions import PersistenceError, InvalidUpdateError, RecordNotFoundError
from kubedriver.kubegroup.record_persistence import ConfigMapRecordPersistence, ConfigMapStorageFormat
from kubedriver.kubegroup.records import EntityGroupRecord, ObjectRecord, RequestRecord, EntityStates, RequestStates, RequestOperations

def json_body(body):
    return json.dumps(body)

class TestConfigMapStorageFormat(unittest.TestCase):

    def test_dump_group_record(self):
        requests = []
        requests.append(RequestRecord('1', RequestOperations.CREATE, state=RequestStates.COMPLETE))
        requests.append(RequestRecord('2', RequestOperations.DELETE, state=RequestStates.FAILED, error='An error'))
        objects = []
        first_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        objects.append(ObjectRecord(first_object_config, state=EntityStates.CREATED))
        second_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigB'
        objects.append(ObjectRecord(second_object_config, state=EntityStates.DELETE_FAILED, error='An error'))
        group = EntityGroupRecord('123', objects, requests=requests)
        dump = ConfigMapStorageFormat().dump_group_record(group)
        self.assertEqual(dump, {
            EntityGroupRecord.UID: '123',
            EntityGroupRecord.OBJECTS: yaml.safe_dump([
                {
                    ObjectRecord.CONFIG: first_object_config,
                    ObjectRecord.STATE: EntityStates.CREATED,
                    ObjectRecord.ERROR: None
                },
                {
                    ObjectRecord.CONFIG: second_object_config,
                    ObjectRecord.STATE: EntityStates.DELETE_FAILED,
                    ObjectRecord.ERROR: 'An error'
                }
            ]),
            EntityGroupRecord.REQUESTS: yaml.safe_dump([
                {
                    RequestRecord.UID: '1',
                    RequestRecord.OPERATION: RequestOperations.CREATE,
                    RequestRecord.STATE: RequestStates.COMPLETE,
                    RequestRecord.ERROR: None
                },
                {
                    RequestRecord.UID: '2',
                    RequestRecord.OPERATION: RequestOperations.DELETE,
                    RequestRecord.STATE: RequestStates.FAILED,
                    RequestRecord.ERROR: 'An error'
                }
            ])
        })
    
    def test_load_group_record(self):
        first_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        second_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigB'
        dump = {
            EntityGroupRecord.UID: '123',
            EntityGroupRecord.OBJECTS: yaml.safe_dump([
                {
                    ObjectRecord.CONFIG: first_object_config,
                    ObjectRecord.STATE: EntityStates.CREATED,
                    ObjectRecord.ERROR: None
                },
                {
                    ObjectRecord.CONFIG: second_object_config,
                    ObjectRecord.STATE: EntityStates.DELETE_FAILED,
                    ObjectRecord.ERROR: 'An error'
                }
            ]),
            EntityGroupRecord.REQUESTS: yaml.safe_dump([
                {
                    RequestRecord.UID: '1',
                    RequestRecord.OPERATION: RequestOperations.CREATE,
                    RequestRecord.STATE: RequestStates.COMPLETE,
                    RequestRecord.ERROR: None
                },
                {
                    RequestRecord.UID: '2',
                    RequestRecord.OPERATION: RequestOperations.DELETE,
                    RequestRecord.STATE: RequestStates.FAILED,
                    RequestRecord.ERROR: 'An error'
                }
            ])
        }
        loaded = ConfigMapStorageFormat().load_group_record(dump)
        self.assertIsInstance(loaded, EntityGroupRecord)
        self.assertEqual(loaded.uid, '123')
        self.assertEqual(len(loaded.objects), 2)
        self.assertEqual(loaded.objects[0].config, first_object_config)
        self.assertEqual(loaded.objects[0].state, EntityStates.CREATED)
        self.assertEqual(loaded.objects[0].error, None)
        self.assertEqual(loaded.objects[1].config, second_object_config)
        self.assertEqual(loaded.objects[1].state, EntityStates.DELETE_FAILED)
        self.assertEqual(loaded.objects[1].error, 'An error')
        self.assertEqual(len(loaded.requests), 2)
        self.assertEqual(loaded.requests[0].uid, '1')
        self.assertEqual(loaded.requests[0].operation, RequestOperations.CREATE)
        self.assertEqual(loaded.requests[0].state, RequestStates.COMPLETE)
        self.assertEqual(loaded.requests[0].error, None)
        self.assertEqual(loaded.requests[1].uid, '2')
        self.assertEqual(loaded.requests[1].operation, RequestOperations.DELETE)
        self.assertEqual(loaded.requests[1].state, RequestStates.FAILED)
        self.assertEqual(loaded.requests[1].error, 'An error')


class TestConfigMapRecordPersistence(unittest.TestCase):

    def setUp(self):
        self.kube_api_ctl = MagicMock()
        self.storage_namespace = 'StorageNamespace'
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace)

    def __build_group_with_two_objects(self, uid='123'):
        object_records = []
        first_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        second_object_config = 'apiVersion: customstuff/v1alpha1\n' + \
                    'kind: MyCustom\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceB\n' + \
                    '  name: MyCustomA'
        object_records.append(ObjectRecord(first_object_config))
        object_records.append(ObjectRecord(second_object_config))
        group_record = EntityGroupRecord(uid, object_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: first_object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            },
            {
                ObjectRecord.CONFIG: second_object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'keg-{0}'.format(uid),
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            EntityGroupRecord.UID: uid,
            EntityGroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            EntityGroupRecord.REQUESTS: yaml.safe_dump([])
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_non_namespaced_object(self, uid='123'):
        object_records = []
        object_config = 'apiVersion: v1\n' + \
                    'kind: Namespace\n' + \
                    'metadata: \n' + \
                    '  name: MyNamespace'
        object_records.append(ObjectRecord(object_config))
        group_record = EntityGroupRecord(uid, object_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'keg-{0}'.format(uid),
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            EntityGroupRecord.UID: uid,
            EntityGroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            EntityGroupRecord.REQUESTS: yaml.safe_dump([])
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_unsafe_uid(self):
        uid = 'Capital-letters'
        object_records = []
        object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        object_records.append(ObjectRecord(object_config))
        group_record = EntityGroupRecord(uid, object_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'keg-capital-letters',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            EntityGroupRecord.UID: 'Capital-letters',
            EntityGroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            EntityGroupRecord.REQUESTS: yaml.safe_dump([])
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_requests(self):
        object_records = []
        first_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        object_records.append(ObjectRecord(first_object_config))
        request_records = []
        request_records.append(RequestRecord('1', RequestOperations.CREATE, state=RequestStates.COMPLETE))
        request_records.append(RequestRecord('2', RequestOperations.DELETE, state=RequestStates.FAILED, error='An error'))
        group_record = EntityGroupRecord('123', object_records, requests=request_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: first_object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_request_records = [
            {
                RequestRecord.UID: '1',
                RequestRecord.OPERATION: RequestOperations.CREATE,
                RequestRecord.STATE: RequestStates.COMPLETE,
                RequestRecord.ERROR: None
            },
            {
                RequestRecord.UID: '2',
                RequestRecord.OPERATION: RequestOperations.DELETE,
                RequestRecord.STATE: RequestStates.FAILED,
                RequestRecord.ERROR: 'An error'
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'keg-123',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            EntityGroupRecord.UID: '123',
            EntityGroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            EntityGroupRecord.REQUESTS: yaml.safe_dump(expected_request_records)
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __rebuild_persistence_with_cm_api_version(self, cm_api_version):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_api_version=cm_api_version)

    def __rebuild_persistence_with_cm_kind(self, cm_kind):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_kind=cm_kind)

    def __rebuild_persistence_with_cm_data_field(self, cm_data_field):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_data_field=cm_data_field)

    def test_create(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_with_requests(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_requests()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_unsafe_uid(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_unsafe_uid()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        with self.assertRaises(PersistenceError) as context:
            self.persistence.create(group_record)
        self.assertEqual(str(context.exception), 'Could not generate valid ConfigMap name for Group \'keg-Capital-letters\': Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid at index 3\']')

    def test_create_customise_cm_api_version(self):
        custom_cm_api_version = 'v2'
        self.__rebuild_persistence_with_cm_api_version(custom_cm_api_version)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v2',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_customise_cm_kind(self):
        custom_cm_kind = 'SuperConfigMap'
        self.__rebuild_persistence_with_cm_kind(custom_cm_kind)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'SuperConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_customise_cm_data_field(self):
        custom_cm_data_field = 'someData'
        self.__rebuild_persistence_with_cm_data_field(custom_cm_data_field)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'someData': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_non_namespaced(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_non_namespaced_object()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)
        
    def test_create_raises_invalid_request_error_on_client_error(self):
        group_record, _, _ = self.__build_group_with_two_objects()
        self.kube_api_ctl.create_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=409, reason='Conflict', data=json_body({'reason': 'AlreadyExists'})))
        with self.assertRaises(InvalidUpdateError) as context:
            self.persistence.create(group_record)
        self.assertEqual(str(context.exception), 'Failed to create record for Group \'123\' as an error occurred: ApiError (409, Conflict) -> AlreadyExists')

    def test_create_raises_persistence_error_on_server_error(self):
        group_record, _, _ = self.__build_group_with_two_objects()
        self.kube_api_ctl.create_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=500, reason='Internal Server Error', data=json_body({'reason': 'Something is not right'})))
        with self.assertRaises(PersistenceError) as context:
            self.persistence.create(group_record)
        self.assertEqual(str(context.exception), 'Failed to create record for Group \'123\' as an error occurred: ApiError (500, Internal Server Error) -> Something is not right')

    def test_get(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)
        self.assertEqual(result_group_record.uid, '123')
        self.assertEqual(len(result_group_record.objects), 2)
        self.assertEqual(result_group_record.objects[0].config, group_record.objects[0].config)
        self.assertEqual(result_group_record.objects[0].state, group_record.objects[0].state)
        self.assertEqual(result_group_record.objects[0].error, group_record.objects[0].error)
        self.assertEqual(result_group_record.objects[1].config, group_record.objects[1].config)
        self.assertEqual(result_group_record.objects[1].state, group_record.objects[1].state)
        self.assertEqual(result_group_record.objects[1].error, group_record.objects[1].error)
    
    def test_get_with_requests(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_requests()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)
        self.assertEqual(result_group_record.uid, '123')
        self.assertEqual(len(result_group_record.requests), 2)
        self.assertEqual(result_group_record.requests[0].uid, group_record.requests[0].uid)
        self.assertEqual(result_group_record.requests[0].operation, group_record.requests[0].operation)
        self.assertEqual(result_group_record.requests[0].state, group_record.requests[0].state)
        self.assertEqual(result_group_record.requests[0].error, group_record.requests[0].error)
        self.assertEqual(result_group_record.requests[1].uid, group_record.requests[1].uid)
        self.assertEqual(result_group_record.requests[1].operation, group_record.requests[1].operation)
        self.assertEqual(result_group_record.requests[1].state, group_record.requests[1].state)
        self.assertEqual(result_group_record.requests[1].error, group_record.requests[1].error)
        
    def test_get_non_namespaced(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_non_namespaced_object()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)
        self.assertEqual(result_group_record.uid, '123')
        self.assertEqual(len(result_group_record.objects), 1)
        self.assertEqual(result_group_record.objects[0].config, group_record.objects[0].config)
        self.assertEqual(result_group_record.objects[0].state, group_record.objects[0].state)
        self.assertEqual(result_group_record.objects[0].error, group_record.objects[0].error)

    def test_get_customise_cm_api_version(self):
        self.__rebuild_persistence_with_cm_api_version('v2')
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v2', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v2', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)
    
    def test_get_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='SuperConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'SuperConfigMap', 'keg-123', namespace=self.storage_namespace)

    def test_get_raises_not_found_error_on_not_found(self):
        self.kube_api_ctl.read_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=404, reason='Not Found', data=json_body({'reason': 'NotFound'})))
        with self.assertRaises(RecordNotFoundError) as context:
            self.persistence.get('123')
        self.assertEqual(str(context.exception), 'Failed to read record for Group \'123\' as an error occurred: ApiError (404, Not Found) -> NotFound')
        
    def test_get_raises_invalid_request_error_on_client_error(self):
        self.kube_api_ctl.read_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=409, reason='Conflict', data=json_body({'reason': 'AlreadyExists'})))
        with self.assertRaises(InvalidUpdateError) as context:
            self.persistence.get('123')
        self.assertEqual(str(context.exception), 'Failed to read record for Group \'123\' as an error occurred: ApiError (409, Conflict) -> AlreadyExists')

    def test_get_raises_persistence_error_on_server_error(self):
        self.kube_api_ctl.read_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=500, reason='Internal Server Error', data=json_body({'reason': 'Something is not right'})))
        with self.assertRaises(PersistenceError) as context:
            self.persistence.get('123')
        self.assertEqual(str(context.exception), 'Failed to read record for Group \'123\' as an error occurred: ApiError (500, Internal Server Error) -> Something is not right')

    def test_delete(self):
        self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)

    def test_delete_customise_cm_api_version(self):
        self.__rebuild_persistence_with_cm_api_version('v2')
        result_group_record = self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v2', 'ConfigMap', 'keg-123', namespace=self.storage_namespace)
    
    def test_delete_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        result_group_record = self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'SuperConfigMap', 'keg-123', namespace=self.storage_namespace)

    def test_delete_raises_not_found_error_on_not_found(self):
        self.kube_api_ctl.delete_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=404, reason='Not Found', data=json_body({'reason': 'NotFound'})))
        with self.assertRaises(RecordNotFoundError) as context:
            self.persistence.delete('123')
        self.assertEqual(str(context.exception), 'Failed to delete record for Group \'123\' as an error occurred: ApiError (404, Not Found) -> NotFound')
        
    def test_delete_raises_invalid_request_error_on_client_error(self):
        self.kube_api_ctl.delete_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=409, reason='Conflict', data=json_body({'reason': 'AlreadyExists'})))
        with self.assertRaises(InvalidUpdateError) as context:
            self.persistence.delete('123')
        self.assertEqual(str(context.exception), 'Failed to delete record for Group \'123\' as an error occurred: ApiError (409, Conflict) -> AlreadyExists')

    def test_delete_raises_persistence_error_on_server_error(self):
        self.kube_api_ctl.delete_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=500, reason='Internal Server Error', data=json_body({'reason': 'Something is not right'})))
        with self.assertRaises(PersistenceError) as context:
            self.persistence.delete('123')
        self.assertEqual(str(context.exception), 'Failed to delete record for Group \'123\' as an error occurred: ApiError (500, Internal Server Error) -> Something is not right')

    def test_update(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_with_requests(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_requests()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_unsafe_uid(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_unsafe_uid()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        with self.assertRaises(PersistenceError) as context:
            self.persistence.update(group_record)
        self.assertEqual(str(context.exception), 'Could not generate valid ConfigMap name for Group \'keg-Capital-letters\': Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid at index 3\']')

    def test_update_customise_cm_api_version(self):
        custom_cm_api_version = 'v2'
        self.__rebuild_persistence_with_cm_api_version(custom_cm_api_version)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v2',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_customise_cm_kind(self):
        custom_cm_kind = 'SuperConfigMap'
        self.__rebuild_persistence_with_cm_kind(custom_cm_kind)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'SuperConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_customise_cm_data_field(self):
        custom_cm_data_field = 'someData'
        self.__rebuild_persistence_with_cm_data_field(custom_cm_data_field)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'someData': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_non_namespaced(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_non_namespaced_object()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(matchers.object_config(expected_config_map), default_namespace=self.storage_namespace)
    
    def test_update_raises_not_found_error_on_not_found(self):
        group_record, _, _ = self.__build_group_with_two_objects()
        self.kube_api_ctl.update_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=404, reason='Not Found', data=json_body({'reason': 'NotFound'})))
        with self.assertRaises(RecordNotFoundError) as context:
            self.persistence.update(group_record)
        self.assertEqual(str(context.exception), 'Failed to update record for Group \'123\' as an error occurred: ApiError (404, Not Found) -> NotFound')
        
    def test_update_raises_invalid_request_error_on_client_error(self):
        group_record, _, _ = self.__build_group_with_two_objects()
        self.kube_api_ctl.update_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=409, reason='Conflict', data=json_body({'reason': 'AlreadyExists'})))
        with self.assertRaises(InvalidUpdateError) as context:
            self.persistence.update(group_record)
        self.assertEqual(str(context.exception), 'Failed to update record for Group \'123\' as an error occurred: ApiError (409, Conflict) -> AlreadyExists')

    def test_update_raises_persistence_error_on_server_error(self):
        group_record, _, _ = self.__build_group_with_two_objects()
        self.kube_api_ctl.update_object.side_effect = ApiException(http_resp=testutils.KubeHttpResponse(status=500, reason='Internal Server Error', data=json_body({'reason': 'Something is not right'})))
        with self.assertRaises(PersistenceError) as context:
            self.persistence.update(group_record)
        self.assertEqual(str(context.exception), 'Failed to update record for Group \'123\' as an error occurred: ApiError (500, Internal Server Error) -> Something is not right')
