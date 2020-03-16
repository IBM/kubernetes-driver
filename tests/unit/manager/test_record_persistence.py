import unittest
import yaml
from unittest.mock import MagicMock
from kubernetes.client import V1ConfigMap
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.manager.record_persistence import ConfigMapRecordPersistence
from kubedriver.manager.object_records import DeployedObjectGroupRecord, DeployedObjectRecord

class ObjectConfigurationMatcher:

    def __init__(self, expected_conf):
        self.expected_conf = expected_conf

    def __eq__(self, other):
        return other.conf == self.expected_conf

    def __str__(self):
        return str(self.expected_conf)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expected_conf!r})'
        
class TestConfigMapRecordPersistence(unittest.TestCase):

    def setUp(self):
        self.kube_api_ctl = MagicMock()
        self.storage_namespace = 'StorageNamespace'
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace)

    def __build_group_with_two_objects(self, identifier='123'):
        object_records = []
        object_records.append(DeployedObjectRecord('v1', 'ConfigMap', 'NamespaceA', 'ConfigA'))
        object_records.append(DeployedObjectRecord('customstuff/v1alpha1', 'MyCustom', 'NamespaceB', 'MyCustomA'))
        group_record = DeployedObjectGroupRecord(identifier, object_records)
        expected_object_records = [
            {
                DeployedObjectRecord.API_VERSION: 'v1',
                DeployedObjectRecord.KIND: 'ConfigMap',
                DeployedObjectRecord.NAMESPACE: 'NamespaceA',
                DeployedObjectRecord.NAME: 'ConfigA'
            },
            {
                DeployedObjectRecord.API_VERSION: 'customstuff/v1alpha1',
                DeployedObjectRecord.KIND: 'MyCustom',
                DeployedObjectRecord.NAMESPACE: 'NamespaceB',
                DeployedObjectRecord.NAME: 'MyCustomA'
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'Kubedriver-Record-123',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            DeployedObjectGroupRecord.IDENTIFIER: '123',
            DeployedObjectGroupRecord.OBJECT_RECORDS: yaml.safe_dump(expected_object_records)
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __build_group_with_non_namespaced_object(self, identifier='123'):
        object_records = []
        object_records.append(DeployedObjectRecord('v1', 'Namespace', None, 'MyNamespace'))
        group_record = DeployedObjectGroupRecord(identifier, object_records)
        expected_object_records = [
            {
                DeployedObjectRecord.API_VERSION: 'v1',
                DeployedObjectRecord.KIND: 'Namespace',
                DeployedObjectRecord.NAMESPACE: None,
                DeployedObjectRecord.NAME: 'MyNamespace'
            }
        ]
        expected_cm_metadata = {
            ObjectConfiguration.NAME: 'Kubedriver-Record-123',
            ObjectConfiguration.NAMESPACE: self.storage_namespace
        }
        expected_cm_data = {
            DeployedObjectGroupRecord.IDENTIFIER: '123',
            DeployedObjectGroupRecord.OBJECT_RECORDS: yaml.safe_dump(expected_object_records)
        }
        return group_record, expected_cm_metadata, expected_cm_data

    def __rebuild_persistence_with_cm_api_version(self, cm_api_version):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_api_version=cm_api_version)

    def __rebuild_persistence_with_cm_kind(self, cm_kind):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_kind=cm_kind)

    def __rebuild_persistence_with_cm_data_field(self, cm_data_field):
        self.persistence = ConfigMapRecordPersistence(self.kube_api_ctl, self.storage_namespace, cm_data_field=cm_data_field)

    def test_persist_object_group_record(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.persist_object_group_record(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_persist_object_group_record_customise_cm_api_version(self):
        custom_cm_api_version = 'v2'
        self.__rebuild_persistence_with_cm_api_version(custom_cm_api_version)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v2',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.persist_object_group_record(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_persist_object_group_record_customise_cm_kind(self):
        custom_cm_kind = 'SuperConfigMap'
        self.__rebuild_persistence_with_cm_kind(custom_cm_kind)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'SuperConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.persist_object_group_record(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_persist_object_group_record_customise_cm_data_field(self):
        custom_cm_data_field = 'someData'
        self.__rebuild_persistence_with_cm_data_field(custom_cm_data_field)
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_two_objects()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'someData': expected_cm_data
        }
        self.persistence.persist_object_group_record(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)

    def test_persist_object_group_record_without_namespace(self):
        group_record, expected_cm_metadata, expected_cm_data = self.__build_group_with_non_namespaced_object()
        expected_config_map = {
            ObjectConfiguration.API_VERSION: 'v1',
            ObjectConfiguration.KIND: 'ConfigMap',
            ObjectConfiguration.METADATA: expected_cm_metadata,
            'data': expected_cm_data
        }
        self.persistence.persist_object_group_record(group_record)
        self.kube_api_ctl.create_object.assert_called_once_with(ObjectConfigurationMatcher(expected_config_map), default_namespace=self.storage_namespace)
        
    def test_get_object_group_record(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get_object_group_record('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)
        self.assertEqual(result_group_record.identifier, '123')
        self.assertEqual(len(result_group_record.object_records), 2)
        self.assertEqual(result_group_record.object_records[0].api_version, group_record.object_records[0].api_version)
        self.assertEqual(result_group_record.object_records[0].kind, group_record.object_records[0].kind)
        self.assertEqual(result_group_record.object_records[0].name, group_record.object_records[0].name)
        self.assertEqual(result_group_record.object_records[0].namespace, group_record.object_records[0].namespace)
        self.assertEqual(result_group_record.object_records[1].api_version, group_record.object_records[1].api_version)
        self.assertEqual(result_group_record.object_records[1].kind, group_record.object_records[1].kind)
        self.assertEqual(result_group_record.object_records[1].name, group_record.object_records[1].name)
        self.assertEqual(result_group_record.object_records[1].namespace, group_record.object_records[1].namespace)

    def test_get_object_group_record_without_namespace(self):
        group_record, cm_metadata, cm_data = self.__build_group_with_non_namespaced_object()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get_object_group_record('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'ConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)
        self.assertEqual(result_group_record.identifier, '123')
        self.assertEqual(len(result_group_record.object_records), 1)
        self.assertEqual(result_group_record.object_records[0].api_version, group_record.object_records[0].api_version)
        self.assertEqual(result_group_record.object_records[0].kind, group_record.object_records[0].kind)
        self.assertEqual(result_group_record.object_records[0].name, group_record.object_records[0].name)
        self.assertIsNone(result_group_record.object_records[0].namespace)

    def test_get_object_group_record_customise_cm_api_version(self):
        self.__rebuild_persistence_with_cm_api_version('v2')
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v2', binary_data=None, data=cm_data, kind='ConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get_object_group_record('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v2', 'ConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)
    
    def test_get_object_group_record_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        group_record, cm_metadata, cm_data = self.__build_group_with_two_objects()
        mock_config_map_result = V1ConfigMap(api_version='v1', binary_data=None, data=cm_data, kind='SuperConfigMap', metadata=cm_metadata)
        self.kube_api_ctl.read_object.return_value = mock_config_map_result
        result_group_record = self.persistence.get_object_group_record('123')
        self.kube_api_ctl.read_object.assert_called_once_with('v1', 'SuperConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)

    def test_delete_object_group_record(self):
        self.persistence.delete_object_group_record('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)

    def test_delete_object_group_record_customise_cm_api_version(self):
        self.__rebuild_persistence_with_cm_api_version('v2')
        result_group_record = self.persistence.delete_object_group_record('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v2', 'ConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)
    
    def test_delete_object_group_record_customise_cm_kind(self):
        self.__rebuild_persistence_with_cm_kind('SuperConfigMap')
        result_group_record = self.persistence.delete_object_group_record('123')
        self.kube_api_ctl.delete_object.assert_called_once_with('v1', 'SuperConfigMap', 'Kubedriver-Record-123', namespace=self.storage_namespace)
