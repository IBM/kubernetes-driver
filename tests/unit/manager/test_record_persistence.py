import unittest
import yaml
from unittest.mock import MagicMock
from kubernetes.client import V1ConfigMap
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.manager.record_persistence import ConfigMapRecordPersistence, ConfigMapStorageFormat
from kubedriver.manager.records import GroupRecord, ObjectRecord, RequestRecord, ObjectStates, RequestStates, RequestOperations

class ObjectConfigurationMatcher:

    def __init__(self, expected_conf):
        self.expected_conf = expected_conf

    def __eq__(self, other):
        return other.config == self.expected_conf

    def __str__(self):
        return str(self.expected_conf)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expected_conf!r})'

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
        objects.append(ObjectRecord(first_object_config, state=ObjectStates.CREATED))
        second_object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigB'
        objects.append(ObjectRecord(second_object_config, state=ObjectStates.DELETE_FAILED, error='An error'))
        group = GroupRecord('123', objects, requests)
        dump = ConfigMapStorageFormat().dump_group_record(group)
        self.assertEqual(dump, {
            GroupRecord.UID: '123',
            GroupRecord.OBJECTS: yaml.safe_dump([
                {
                    ObjectRecord.CONFIG: first_object_config,
                    ObjectRecord.STATE: ObjectStates.CREATED,
                    ObjectRecord.ERROR: None
                },
                {
                    ObjectRecord.CONFIG: second_object_config,
                    ObjectRecord.STATE: ObjectStates.DELETE_FAILED,
                    ObjectRecord.ERROR: 'An error'
                }
            ]),
            GroupRecord.REQUESTS: yaml.safe_dump([
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
            GroupRecord.UID: '123',
            GroupRecord.OBJECTS: yaml.safe_dump([
                {
                    ObjectRecord.CONFIG: first_object_config,
                    ObjectRecord.STATE: ObjectStates.CREATED,
                    ObjectRecord.ERROR: None
                },
                {
                    ObjectRecord.CONFIG: second_object_config,
                    ObjectRecord.STATE: ObjectStates.DELETE_FAILED,
                    ObjectRecord.ERROR: 'An error'
                }
            ]),
            GroupRecord.REQUESTS: yaml.safe_dump([
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
        self.assertIsInstance(loaded, GroupRecord)
        self.assertEqual(loaded.uid, '123')
        self.assertEqual(len(loaded.objects), 2)
        self.assertEqual(loaded.objects[0].config, first_object_config)
        self.assertEqual(loaded.objects[0].state, ObjectStates.CREATED)
        self.assertEqual(loaded.objects[0].error, None)
        self.assertEqual(loaded.objects[1].config, second_object_config)
        self.assertEqual(loaded.objects[1].state, ObjectStates.DELETE_FAILED)
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
        group_record = GroupRecord(uid, object_records)
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
            ObjectConfiguration.NAME: 'kdr-{0}'.format(uid),
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            GroupRecord.UID: uid,
            GroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            GroupRecord.REQUESTS: yaml.safe_dump([])
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_non_namespaced_object(self, uid='123'):
        object_records = []
        object_config = 'apiVersion: v1\n' + \
                    'kind: Namespace\n' + \
                    'metadata: \n' + \
                    '  name: MyNamespace'
        object_records.append(ObjectRecord(object_config))
        group_record = GroupRecord(uid, object_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'kdr-{0}'.format(uid),
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            GroupRecord.UID: uid,
            GroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            GroupRecord.REQUESTS: yaml.safe_dump([])
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_unsafe_uid(self):
        uid = 'Capital-letters-and_underscore-removed'
        object_records = []
        object_config = 'apiVersion: v1\n' + \
                    'kind: ConfigMap\n' + \
                    'metadata: \n' + \
                    '  namespace: NamespaceA\n' + \
                    '  name: ConfigA'
        object_records.append(ObjectRecord(object_config))
        group_record = GroupRecord(uid, object_records)
        expected_object_records = [
            {
                ObjectRecord.CONFIG: object_config,
                ObjectRecord.STATE: 'Pending',
                ObjectRecord.ERROR: None
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'kdr-capital-letters-and-underscore-removed',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            GroupRecord.UID: 'Capital-letters-and_underscore-removed',
            GroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            GroupRecord.REQUESTS: yaml.safe_dump([])
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
        group_record = GroupRecord('123', object_records, request_records)
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
            ObjectConfiguration.NAME: 'kdr-123',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            GroupRecord.UID: '123',
            GroupRecord.OBJECTS: yaml.safe_dump(expected_object_records),
            GroupRecord.REQUESTS: yaml.safe_dump(expected_request_records)
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
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_with_requests(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_requests()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_unsafe_uid(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_unsafe_uid()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_create_non_namespaced(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_non_namespaced_object()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.create(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)
        
    def test_get(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)
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
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)
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
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)
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
        self.kube_api_ctl.read_object.assert_called_once_with('v2', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)
    
    def test_get_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='SuperConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'SuperConfigMap', 'kdr-123', namespace=self.storage_namespace)

    def test_delete(self):
        self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)

    def test_delete_customise_cm_api_version(self):
        self.__rebuild_persistence_with_cm_api_version('v2')
        result_group_record = self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v2', 'ConfigMap', 'kdr-123', namespace=self.storage_namespace)
    
    def test_delete_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        result_group_record = self.persistence.delete('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'SuperConfigMap', 'kdr-123', namespace=self.storage_namespace)

    def test_update(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_with_requests(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_requests()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_unsafe_uid(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_unsafe_uid()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

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
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_update_non_namespaced(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_non_namespaced_object()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.update(group_record)
        self.kube_api_ctl.update_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)
        