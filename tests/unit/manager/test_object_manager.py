import unittest
import copy
from unittest.mock import MagicMock, call
from kubedriver.location import KubeDeploymentLocation
from kubedriver.manager.object_manager import KubeObjectManager, CREATE_JOB, DELETE_JOB
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeobjects.object_group import ObjectConfigurationGroup
from kubedriver.manager.records import GroupRecord, ObjectRecord, RequestRecord, ObjectStates, RequestStates, RequestOperations

class CopyArgsMagicMock(MagicMock):
    def _mock_call(_mock_self, *args, **kwargs):
        """
        Store copies of arguments passed into calls to the
        mock object, instead of storing references to the original argument objects.
        """
        return super()._mock_call(*copy.deepcopy(args), **copy.deepcopy(kwargs))

class ObjectConfigurationMatcher:

    def __init__(self, expected_conf):
        self.expected_conf = expected_conf

    def __eq__(self, other):
        return other.config == self.expected_conf

    def __str__(self):
        return str(self.expected_conf)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expected_conf!r})'

class GroupRecordMatcher:

    def __init__(self, expected_group_record):
        self.expected_group_record = expected_group_record

    def __eq__(self, other):
        return self.__matches_group_record(other, self.expected_group_record) 

    def __str__(self):
        return str(self.expected_group_record)

    def __repr__(self):
        return f'{self.expected_group_record!r}'

    def __matches_group_record(self, first_record, second_record):
        if first_record.uid != second_record.uid:
            return False
        if len(first_record.objects) != len(second_record.objects):
            return False
        for idx in range(len(first_record.objects)):
            matches = self.__matches_object_record(first_record.objects[idx], second_record.objects[idx])
            if not matches:
                return False
        if len(first_record.requests) != len(second_record.requests):
            return False
        for idx in range(len(first_record.requests)):
            matches = self.__matches_request_record(first_record.requests[idx], second_record.requests[idx])
            if not matches:
                return False
        return True

    def __matches_object_record(self, first_record, second_record):
        if first_record.config != second_record.config:
            return False
        if first_record.state != second_record.state:
            return False
        if first_record.error != second_record.error:
            return False
        return True

    def __matches_request_record(self, first_record, second_record):
        if first_record.uid != second_record.uid:
            return False
        if first_record.operation != second_record.operation:
            return False
        if first_record.state != second_record.state:
            return False
        if first_record.error != second_record.error:
            return False
        return True

class TestKubeObjectManager(unittest.TestCase):
    
    def setUp(self):
        self.kube_api_ctl = MagicMock()
        self.record_persistence = self.__mock_persistence()
        self.job_queue = self.__mock_job_queue()
        self.context_management = MagicMock(api_ctl=self.kube_api_ctl, record_persistence=self.record_persistence)
        self.kube_location = KubeDeploymentLocation('Test', 'config')
        self.context = MagicMock(location=self.kube_location, record_persistence=self.record_persistence, api_ctl=self.kube_api_ctl)
        self.context_management.load.return_value = self.context
        self.object_manager = KubeObjectManager(self.context_management, self.job_queue)

    def __mock_persistence(self):
        mock_persistence = CopyArgsMagicMock()
        store = {}
        def create(group_record):
            store[group_record.uid] = copy.deepcopy(group_record)
        def get(uid):
            if uid not in store:
                raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
            return copy.deepcopy(store[uid])
        def delete(uid):
            if uid not in store:
                raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
            store.pop(uid)
        def update(group_record):
            if group_record.uid not in store:
                raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
            store[group_record.uid] = copy.deepcopy(group_record)
        mock_persistence.create.side_effect = create
        mock_persistence.get.side_effect = get
        mock_persistence.delete.side_effect = delete
        mock_persistence.update.side_effect = update
        return mock_persistence

    def __mock_job_queue(self):
        mock_job_queue = MagicMock()
        mock_job_queue_state = []
        job_handlers = {}
        def register_handler(job_type, func):
            job_handlers[job_type] = func
        mock_job_queue.register_job_handler.side_effect = register_handler
        def queue_job(job):
            mock_job_queue_state.append(job)
        mock_job_queue.queue_job.side_effect = queue_job
        def process_next_job():
            if len(mock_job_queue_state) > 0:
                job = mock_job_queue_state.pop(0)
                job_handlers[job['job_type']](job)
            else:
                raise IndexError('No jobs in queue')
        mock_job_queue.process_next_job.side_effect = process_next_job
        return mock_job_queue

    def __build_group_with_two_objects(self):
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
        group = ObjectConfigurationGroup('123', object_confs)
        return group

    def __build_created_group_record_with_two_objects(self):
        group = self.__build_group_with_two_objects()
        group_record = GroupRecord(group.identifier,
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        return group_record

    def __build_group_with_namespaced_object(self):
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
                'name': 'TestCM-B',
                'namespace': 'SomeNamespace'
            }
        }))
        group = ObjectConfigurationGroup('123', object_confs)
        return group

    def __build_created_group_record_with_namespaced_object(self):
        group = self.__build_group_with_namespaced_object()
        group_record = GroupRecord(group.identifier,
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        return group_record

    def __build_create_failed_group_record(self):
        group = self.__build_group_with_two_objects()
        group_record = GroupRecord(group.identifier,
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.CREATE_FAILED, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.FAILED, error=None)
            ]
        )
        return group_record

    def __configure_mock_create_failure(self, on_matching_config):
        def side_effect(config, *args, **kwargs):
            if on_matching_config == config.config:
                raise ValueError('A mock error')
        self.kube_api_ctl.create_object.side_effect = side_effect

    def __configure_mock_delete_failure(self, on_matching_config):
        obj_config = ObjectConfiguration(on_matching_config)
        def side_effect(api_version, kind, name, *args, **kwargs):
            if api_version == obj_config.api_version and kind == obj_config.kind and name == obj_config.name:
                raise ValueError('A mock error')
        self.kube_api_ctl.delete_object.side_effect = side_effect

    def test_init_registers_job_handler(self):
        self.job_queue.register_job_handler.assert_has_calls([
            call(CREATE_JOB, self.object_manager._KubeObjectManager__handler_for_job),
            call(DELETE_JOB, self.object_manager._KubeObjectManager__handler_for_job),
        ])

    def test_create_group_queues_job(self):
        group = self.__build_group_with_two_objects()
        request_id = self.object_manager.create_group(self.kube_location, group)
        self.context_management.load.assert_called_once_with(self.kube_location)
        expected_group_record = GroupRecord('123',
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.PENDING, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.PENDING, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.PENDING, error=None)
            ]
        )
        self.context.record_persistence.create.assert_called_once_with(GroupRecordMatcher(expected_group_record))
        self.job_queue.queue_job.assert_called_once_with({
            'job_type': CREATE_JOB,
            'group_uid': '123',
            'request_uid': request_id,
            'kube_location': self.kube_location.to_dict()
        })

    def test_process_create_job_updates_records(self):
        group = self.__build_group_with_two_objects()
        request_id = self.object_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.record_persistence.get.assert_called_once_with('123')
        expected_in_progress_record = GroupRecord('123',
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.PENDING, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.PENDING, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.IN_PROGRESS, error=None)
            ]
        )
        expected_complete_record = GroupRecord('123',
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(group.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        self.context.record_persistence.update.assert_has_calls([
            call(GroupRecordMatcher(expected_in_progress_record)),
            call(GroupRecordMatcher(expected_complete_record))
        ])
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)

    def test_process_create_job_creates_objects(self):
        group = self.__build_group_with_two_objects()
        request_id = self.object_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.api_ctl.create_object.assert_has_calls([
            call(ObjectConfigurationMatcher(group.objects[0].config), default_namespace='default'),
            call(ObjectConfigurationMatcher(group.objects[1].config), default_namespace='default')
        ])
        self.assertEqual(len(self.context.api_ctl.create_object.call_args_list), 2)

    def test_process_create_job_creates_objects_using_default_location_namespace(self):
        self.kube_location.default_object_namespace = 'AltDefault'
        group = self.__build_group_with_two_objects()
        request_id = self.object_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.api_ctl.create_object.assert_has_calls([
            call(ObjectConfigurationMatcher(group.objects[0].config), default_namespace='AltDefault'),
            call(ObjectConfigurationMatcher(group.objects[1].config), default_namespace='AltDefault')
        ])
        self.assertEqual(len(self.context.api_ctl.create_object.call_args_list), 2)

    def test_process_create_job_updates_record_with_failure(self):
        group = self.__build_group_with_two_objects()
        self.__configure_mock_create_failure(group.objects[0].config)
        request_id = self.object_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        expected_complete_record = GroupRecord('123',
            objects=[
                ObjectRecord(group.objects[0].config, state=ObjectStates.CREATE_FAILED, error='A mock error'),
                ObjectRecord(group.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[1]
        self.assertEqual(last_update_args[0], GroupRecordMatcher(expected_complete_record))
        
    def test_delete_group_queues_job(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.context_management.load.assert_called_once_with(self.kube_location)
        expected_group_record = GroupRecord(existing_group_record.uid,
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(existing_group_record.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.PENDING, error=None)
            ]
        )
        self.context.record_persistence.update.assert_called_once_with(GroupRecordMatcher(expected_group_record))
        self.job_queue.queue_job.assert_called_once_with({
            'job_type': DELETE_JOB,
            'group_uid': '123',
            'request_uid': request_id,
            'kube_location': self.kube_location.to_dict()
        })

    def test_process_delete_job_updates_records(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.job_queue.process_next_job()
        expected_pending_record = GroupRecord('123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(existing_group_record.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.PENDING, error=None)
            ]
        )
        expected_in_progress_record = GroupRecord('123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=ObjectStates.CREATED, error=None),
                ObjectRecord(existing_group_record.objects[1].config, state=ObjectStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.IN_PROGRESS, error=None)
            ]
        )
        expected_complete_record = GroupRecord('123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=ObjectStates.DELETED, error=None),
                ObjectRecord(existing_group_record.objects[1].config, state=ObjectStates.DELETED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        self.context.record_persistence.update.assert_has_calls([
            call(GroupRecordMatcher(expected_pending_record)),
            call(GroupRecordMatcher(expected_in_progress_record)),
            call(GroupRecordMatcher(expected_complete_record))
        ])
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 3)

    def test_process_delete_job_deletes_objects(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        self.context.api_ctl.delete_object.assert_has_calls([
            call(first_object_configuration.api_version, first_object_configuration.kind, first_object_configuration.name, namespace='default'),
            call(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='default')
        ])
        self.assertEqual(len(self.context.api_ctl.delete_object.call_args_list), 2)

    def test_process_delete_job_namespaced_object(self):
        existing_group_record = self.__build_created_group_record_with_namespaced_object()
        self.record_persistence.create(existing_group_record)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        self.context.api_ctl.delete_object.assert_has_calls([
            call(first_object_configuration.api_version, first_object_configuration.kind, first_object_configuration.name, namespace='default'),
            call(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='SomeNamespace')
        ])
        self.assertEqual(len(self.context.api_ctl.delete_object.call_args_list), 2)

    def test_process_delete_job_updates_record_with_failure(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        self.__configure_mock_delete_failure(existing_group_record.objects[0].config)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.job_queue.process_next_job()
        expected_complete_record = GroupRecord('123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=ObjectStates.DELETE_FAILED, error='A mock error'),
                ObjectRecord(existing_group_record.objects[1].config, state=ObjectStates.DELETED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 3)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[2]
        self.assertEqual(last_update_args[0], GroupRecordMatcher(expected_complete_record))
        
    def test_process_delete_job_ignores_objects_not_created(self):
        existing_group_record = self.__build_create_failed_group_record()
        self.record_persistence.create(existing_group_record)
        request_id = self.object_manager.delete_group(self.kube_location, '123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        # First object failed to create so we don't delete
        self.context.api_ctl.delete_object.assert_called_once_with(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='default')
        