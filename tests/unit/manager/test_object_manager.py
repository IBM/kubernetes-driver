import unittest
from unittest.mock import MagicMock, call
from kubedriver.manager.object_manager import KubeObjectManager
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeobjects.object_group import ObjectConfigurationGroup
from kubedriver.manager.object_records import DeployedObjectGroupRecord, DeployedObjectRecord

class ObjectConfigurationMatcher:

    def __init__(self, expected_conf):
        self.expected_conf = expected_conf

    def __eq__(self, other):
        return other.conf == self.expected_conf

    def __str__(self):
        return str(self.expected_conf)

    def __repr__(self):
        return f'{self.expected_conf!r}'
        

class ObjectRecordMatcher:

    def __init__(self, expected_record):
        self.expected_record = expected_record

    def __eq__(self, other):
        return self.__matches_object_record(other, self.expected_record) 

    def __str__(self):
        return str(self.expected_record)

    def __repr__(self):
        return f'{self.expected_record!r}'

    def __matches_object_record(self, first_record, second_record):
        if first_record.api_version != second_record.api_version:
            return False
        if first_record.kind != second_record.kind:
            return False
        if first_record.namespace != second_record.namespace:
            return False
        if first_record.name != second_record.name:
            return False
        return True

class ObjectGroupRecordMatcher:

    def __init__(self, expected_group_record):
        self.expected_group_record = expected_group_record

    def __eq__(self, other):
        return self.__matches_group_record(other, self.expected_group_record) 

    def __str__(self):
        return str(self.expected_group_record)

    def __repr__(self):
        return f'{self.expected_group_record!r}'

    def __matches_group_record(self, first_record, second_record):
        if first_record.identifier != second_record.identifier:
            return False
        if len(first_record.object_records) != len(second_record.object_records):
            return False
        for idx in range(len(first_record.object_records)):
            matches = self.__matches_object_record(first_record.object_records[idx], second_record.object_records[idx])
            if not matches:
                return False
        return True

    def __matches_object_record(self, first_record, second_record):
        if first_record.api_version != second_record.api_version:
            return False
        if first_record.kind != second_record.kind:
            return False
        if first_record.namespace != second_record.namespace:
            return False
        if first_record.name != second_record.name:
            return False
        return True

class TestKubeObjectManager(unittest.TestCase):
    
    def setUp(self):
        self.kube_api_ctl = MagicMock()
        self.record_persistence = MagicMock()
        self.object_manager = KubeObjectManager(self.kube_api_ctl, self.record_persistence)

    def __build_group_with_two_objects(self, identifier='123'):
        object_confs = []
        object_confs.append(ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'TestCM-A'
            }
        }))
        object_confs.append(ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'TestCM-B'
            }
        }))
        group = ObjectConfigurationGroup(identifier, object_confs)
        object_records = []
        object_records.append(DeployedObjectRecord('v1', 'ConfigMap', 'default', 'TestCM-A'))
        object_records.append(DeployedObjectRecord('v1', 'ConfigMap', 'default', 'TestCM-B'))
        expected_group_record = DeployedObjectGroupRecord(identifier, object_records)
        return group, expected_group_record

    def __build_group_with_non_namespaced_object(self, identifier='123'):
        object_confs = []
        object_confs.append(ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'PersistentVolume',
            'metadata': {
                'name': 'PV-A'
            }
        }))
        group = ObjectConfigurationGroup(identifier, object_confs)
        object_records = []
        object_records.append(DeployedObjectRecord('v1', 'PersistentVolume', None, 'PV-A'))
        expected_group_record = DeployedObjectGroupRecord(identifier, object_records)
        return group, expected_group_record

    def test_create_object_group(self):
        object_group, expected_group_record = self.__build_group_with_two_objects()
        self.object_manager.create_object_group(object_group)
        self.record_persistence.persist_object_group_record.assert_called_once_with(ObjectGroupRecordMatcher(expected_group_record))
        expected_create_calls = [
            call(object_group.objects[0], default_namespace='default'),
            call(object_group.objects[1], default_namespace='default')
        ]
        self.kube_api_ctl.create_object.assert_has_calls(expected_create_calls)
        self.assertEqual(len(self.kube_api_ctl.create_object.call_args_list), 2)

    def test_create_object_group_with_non_namespaced_object(self):
        object_group, expected_group_record = self.__build_group_with_non_namespaced_object()
        self.kube_api_ctl.is_object_namespaced.return_value = False
        self.object_manager.create_object_group(object_group)
        self.record_persistence.persist_object_group_record.assert_called_once_with(ObjectGroupRecordMatcher(expected_group_record))
        self.kube_api_ctl.create_object.assert_called_once_with(object_group.objects[0], default_namespace='default')
