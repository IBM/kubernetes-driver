import unittest
from unittest.mock import MagicMock, call, patch
import tests.matchers as matchers
import tests.utils as testutils
from kubedriver.location import KubeDeploymentLocation
from kubedriver.kubegroup.group_manager import EntityGroupManager, CREATE_JOB, DELETE_JOB
from kubedriver.kubegroup.entity_group import EntityGroup
from kubedriver.kubegroup.records import EntityGroupRecord, ObjectRecord, HelmReleaseRecord, RequestRecord, EntityStates, RequestStates, RequestOperations
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.helmobjects.helm_release_config import HelmReleaseConfiguration

class TestEntityGroupManager(unittest.TestCase):
    
    def setUp(self):
        self.kube_api_ctl = MagicMock()
        self.helm_client = MagicMock()
        self.record_persistence = testutils.mem_persistence_mock.create()
        self.job_queue = testutils.controlled_job_queue_mock.create()
        self.context_management = MagicMock(api_ctl=self.kube_api_ctl, record_persistence=self.record_persistence)
        self.kube_location = KubeDeploymentLocation('Test', 'config')
        self.context = MagicMock(location=self.kube_location, record_persistence=self.record_persistence, api_ctl=self.kube_api_ctl, helm_client=self.helm_client)
        self.context_management.load.return_value = self.context
        self.group_manager = EntityGroupManager(self.context_management, self.job_queue)

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
        group = EntityGroup('test-123', object_confs)
        return group

    def __build_created_group_record_with_two_objects(self):
        group = self.__build_group_with_two_objects()
        group_record = EntityGroupRecord(group.uid,
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATED, error=None),
                ObjectRecord(group.objects[1].data, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        return group_record

    def __build_created_group_record_with_object_and_helm_release(self):
        group = self.__build_group_with_object_and_helm_release()
        group_record = EntityGroupRecord(group.uid,
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATED, error=None)
            ],
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.CREATED, error=None)
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
        group = EntityGroup('test-123', object_confs)
        return group

    def __build_created_group_record_with_namespaced_object(self):
        group = self.__build_group_with_namespaced_object()
        group_record = EntityGroupRecord(group.uid,
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATED, error=None),
                ObjectRecord(group.objects[1].data, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        return group_record

    def __build_create_failed_group_record_with_objects(self):
        group = self.__build_group_with_two_objects()
        group_record = EntityGroupRecord(group.uid,
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATE_FAILED, error=None),
                ObjectRecord(group.objects[1].data, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.FAILED, error=None)
            ]
        )
        return group_record

    def __build_create_failed_group_record_with_helm_releases(self):
        group = self.__build_group_with_two_helm_releases()
        group_record = EntityGroupRecord(group.uid,
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.CREATE_FAILED, error='An error'),
                HelmReleaseRecord(group.helm_releases[1].chart, group.helm_releases[1].name, group.helm_releases[1].namespace, group.helm_releases[1].values, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.FAILED, error=None)
            ]
        )
        return group_record

    def __build_group_with_object_and_helm_release(self):
        object_confs = []
        object_confs.append(ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'TestCM-A'
            }
        }))
        helm_releases = []
        helm_releases.append(HelmReleaseConfiguration('mychart-a.tgz', 'release-a', 'namespace-a', 'someValue: 123'))
        group = EntityGroup('test-123', objects=object_confs, helm_releases=helm_releases)
        return group

    def __build_group_with_two_helm_releases(self):
        helm_releases = []
        helm_releases.append(HelmReleaseConfiguration('mychart-a.tgz', 'release-a', 'namespace-a', 'someValue: 123'))
        helm_releases.append(HelmReleaseConfiguration('mychart-b.tgz', 'release-b', 'namespace-b', 'someValue: 456'))
        group = EntityGroup('test-123', helm_releases=helm_releases)
        return group

    def __build_created_group_record_with_two_helm_releases(self):
        group = self.__build_group_with_two_helm_releases()
        group_record = EntityGroupRecord(group.uid,
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.CREATED, error=None),
                HelmReleaseRecord(group.helm_releases[1].chart, group.helm_releases[1].name, group.helm_releases[1].namespace, group.helm_releases[1].values, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        return group_record

    def __configure_mock_create_object_failure(self, on_matching_config):
        def side_effect(config, *args, **kwargs):
            if on_matching_config == config.data:
                raise testutils.MockedError('A mock create error')
        self.kube_api_ctl.create_object.side_effect = side_effect

    def __configure_mock_delete_object_failure(self, on_matching_config):
        obj_config = ObjectConfiguration(on_matching_config)
        def side_effect(api_version, kind, name, *args, **kwargs):
            if api_version == obj_config.api_version and kind == obj_config.kind and name == obj_config.name:
                raise testutils.MockedError('A mock delete error')
        self.kube_api_ctl.delete_object.side_effect = side_effect

    def __configure_mock_helm_install_failure(self, on_matching_helm_release_name):
        def side_effect(chart, name, *args, **kwargs):
            if on_matching_helm_release_name == name:
                raise testutils.MockedError('A mock install error')
        self.helm_client.install.side_effect = side_effect

    def __configure_mock_helm_purge_failure(self, on_matching_helm_release_name):
        def side_effect(name):
            if on_matching_helm_release_name == name:
                raise testutils.MockedError('A mock purge error')
        self.helm_client.purge.side_effect = side_effect

    def test_init_registers_job_handler(self):
        self.job_queue.register_job_handler.assert_has_calls([
            call(CREATE_JOB, self.group_manager._EntityGroupManager__handler_for_job),
            call(DELETE_JOB, self.group_manager._EntityGroupManager__handler_for_job),
        ])

    def test_create_group_queues_job(self):
        group = self.__build_group_with_two_objects()
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.context_management.load.assert_called_once_with(self.kube_location)
        expected_group_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.PENDING, error=None),
                ObjectRecord(group.objects[1].data, state=EntityStates.PENDING, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.PENDING, error=None)
            ]
        )
        self.context.record_persistence.create.assert_called_once_with(matchers.entity_group_record(expected_group_record))
        self.job_queue.queue_job.assert_called_once_with({
            'job_type': CREATE_JOB,
            'group_uid': 'test-123',
            'request_uid': request_id,
            'kube_location': self.kube_location.to_dict()
        })

    def test_process_create_job_updates_records(self):
        group = self.__build_group_with_object_and_helm_release()
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.record_persistence.get.assert_called_once_with('test-123')
        expected_in_progress_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.PENDING, error=None),
            ],
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.PENDING),
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.IN_PROGRESS, error=None)
            ]
        )
        expected_complete_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATED, error=None)
            ],
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.CREATED),
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        self.context.record_persistence.update.assert_has_calls([
            call(matchers.entity_group_record(expected_in_progress_record)),
            call(matchers.entity_group_record(expected_complete_record))
        ])
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)

    def test_process_create_job_creates_objects(self):
        group = self.__build_group_with_two_objects()
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.api_ctl.create_object.assert_has_calls([
            call(matchers.object_config(group.objects[0].data), default_namespace='default'),
            call(matchers.object_config(group.objects[1].data), default_namespace='default')
        ])
        self.assertEqual(len(self.context.api_ctl.create_object.call_args_list), 2)

    def test_process_create_job_creates_objects_using_default_location_namespace(self):
        self.kube_location.default_object_namespace = 'AltDefault'
        group = self.__build_group_with_two_objects()
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.api_ctl.create_object.assert_has_calls([
            call(matchers.object_config(group.objects[0].data), default_namespace='AltDefault'),
            call(matchers.object_config(group.objects[1].data), default_namespace='AltDefault')
        ])
        self.assertEqual(len(self.context.api_ctl.create_object.call_args_list), 2)

    def test_process_create_job_updates_record_with_object_failure(self):
        group = self.__build_group_with_two_objects()
        self.__configure_mock_create_object_failure(group.objects[0].data)
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        expected_complete_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(group.objects[0].data, state=EntityStates.CREATE_FAILED, error='A mock create error'),
                ObjectRecord(group.objects[1].data, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock create error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[1]
        self.assertEqual(last_update_args[0], matchers.entity_group_record(expected_complete_record))

    def test_process_create_job_creates_helm_releases(self):
        group = self.__build_group_with_two_helm_releases()
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        self.context.helm_client.install.assert_has_calls([
            call('mychart-a.tgz', 'release-a', 'namespace-a', 'someValue: 123'),
            call('mychart-b.tgz', 'release-b', 'namespace-b', 'someValue: 456')
        ])
        self.assertEqual(len(self.context.helm_client.install.call_args_list), 2)

    def test_process_create_job_updates_record_with_helm_failure(self):
        group = self.__build_group_with_two_helm_releases()
        self.__configure_mock_helm_install_failure(group.helm_releases[0].name)
        request_id = self.group_manager.create_group(self.kube_location, group)
        self.job_queue.process_next_job()
        expected_complete_record = EntityGroupRecord('test-123',
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.CREATE_FAILED, error='A mock install error'),
                HelmReleaseRecord(group.helm_releases[1].chart, group.helm_releases[1].name, group.helm_releases[1].namespace, group.helm_releases[1].values, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock install error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[1]
        self.assertEqual(last_update_args[0], matchers.entity_group_record(expected_complete_record))

    def test_delete_group_queues_job(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.context_management.load.assert_called_once_with(self.kube_location)
        expected_group_record = EntityGroupRecord(existing_group_record.uid,
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=EntityStates.CREATED, error=None),
                ObjectRecord(existing_group_record.objects[1].config, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.PENDING, error=None)
            ]
        )
        self.context.record_persistence.update.assert_called_once_with(matchers.entity_group_record(expected_group_record))
        self.job_queue.queue_job.assert_called_once_with({
            'job_type': DELETE_JOB,
            'group_uid': 'test-123',
            'request_uid': request_id,
            'kube_location': self.kube_location.to_dict()
        })

    def test_process_delete_job_updates_records(self):
        existing_group_record = self.__build_created_group_record_with_object_and_helm_release()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        expected_pending_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=EntityStates.CREATED, error=None)
            ],
            helm_releases=[
                HelmReleaseRecord(existing_group_record.helm_releases[0].chart, existing_group_record.helm_releases[0].name, existing_group_record.helm_releases[0].namespace, existing_group_record.helm_releases[0].values, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.PENDING, error=None)
            ]
        )
        expected_in_progress_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=EntityStates.CREATED, error=None)
            ],
            helm_releases=[
                HelmReleaseRecord(existing_group_record.helm_releases[0].chart, existing_group_record.helm_releases[0].name, existing_group_record.helm_releases[0].namespace, existing_group_record.helm_releases[0].values, state=EntityStates.CREATED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.IN_PROGRESS, error=None)
            ]
        )
        expected_complete_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=EntityStates.DELETED, error=None)
            ],
            helm_releases=[
                HelmReleaseRecord(existing_group_record.helm_releases[0].chart, existing_group_record.helm_releases[0].name, existing_group_record.helm_releases[0].namespace, existing_group_record.helm_releases[0].values, state=EntityStates.DELETED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.COMPLETE, error=None)
            ]
        )
        self.context.record_persistence.update.assert_has_calls([
            call(matchers.entity_group_record(expected_pending_record)),
            call(matchers.entity_group_record(expected_in_progress_record)),
            call(matchers.entity_group_record(expected_complete_record))
        ])
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 3)

    def test_process_delete_job_deletes_objects(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        self.context.api_ctl.delete_object.assert_has_calls([
            call(first_object_configuration.api_version, first_object_configuration.kind, first_object_configuration.name, namespace='default'),
            call(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='default')
        ])
        self.assertEqual(len(self.context.api_ctl.delete_object.call_args_list), 2)

    def test_process_delete_job_purges_helm_releases(self):
        existing_group_record = self.__build_created_group_record_with_two_helm_releases()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        self.context.helm_client.purge.assert_has_calls([
            call(existing_group_record.helm_releases[0].name),
            call(existing_group_record.helm_releases[1].name)
        ])

    def test_process_delete_job_namespaced_object(self):
        existing_group_record = self.__build_created_group_record_with_namespaced_object()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        self.context.api_ctl.delete_object.assert_has_calls([
            call(first_object_configuration.api_version, first_object_configuration.kind, first_object_configuration.name, namespace='default'),
            call(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='SomeNamespace')
        ])
        self.assertEqual(len(self.context.api_ctl.delete_object.call_args_list), 2)

    def test_process_delete_job_updates_record_with_object_failure(self):
        existing_group_record = self.__build_created_group_record_with_two_objects()
        self.record_persistence.create(existing_group_record)
        self.__configure_mock_delete_object_failure(existing_group_record.objects[0].config)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        expected_complete_record = EntityGroupRecord('test-123',
            objects=[
                ObjectRecord(existing_group_record.objects[0].config, state=EntityStates.DELETE_FAILED, error='A mock delete error'),
                ObjectRecord(existing_group_record.objects[1].config, state=EntityStates.DELETED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock delete error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 3)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[2]
        self.assertEqual(last_update_args[0], matchers.entity_group_record(expected_complete_record))

    def test_process_delete_job_updates_record_with_helm_failure(self):
        existing_group_record = self.__build_created_group_record_with_two_helm_releases()
        self.record_persistence.create(existing_group_record)
        self.__configure_mock_helm_purge_failure(existing_group_record.helm_releases[0].name)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        expected_complete_record = EntityGroupRecord('test-123',
            helm_releases=[
                HelmReleaseRecord(existing_group_record.helm_releases[0].chart, existing_group_record.helm_releases[0].name, existing_group_record.helm_releases[0].namespace, existing_group_record.helm_releases[0].values, state=EntityStates.DELETE_FAILED, error='A mock purge error'),
                HelmReleaseRecord(existing_group_record.helm_releases[1].chart, existing_group_record.helm_releases[1].name, existing_group_record.helm_releases[1].namespace, existing_group_record.helm_releases[1].values, state=EntityStates.DELETED, error=None)
            ],
            requests=[
                RequestRecord('create123', RequestOperations.CREATE, state=RequestStates.COMPLETE, error=None),
                RequestRecord(request_id, RequestOperations.DELETE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - A mock purge error')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 3)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[2]
        self.assertEqual(last_update_args[0], matchers.entity_group_record(expected_complete_record))

    def test_process_delete_job_ignores_objects_not_created(self):
        existing_group_record = self.__build_create_failed_group_record_with_objects()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        first_object_configuration = ObjectConfiguration(existing_group_record.objects[0].config)
        second_object_configuration = ObjectConfiguration(existing_group_record.objects[1].config)
        # First object failed to create so we don't delete
        self.context.api_ctl.delete_object.assert_called_once_with(second_object_configuration.api_version, second_object_configuration.kind, second_object_configuration.name, namespace='default')
    
    def test_process_delete_job_ignores_helm_releases_not_created(self):
        existing_group_record = self.__build_create_failed_group_record_with_helm_releases()
        self.record_persistence.create(existing_group_record)
        request_id = self.group_manager.delete_group(self.kube_location, 'test-123')
        self.job_queue.process_next_job()
        # First helm release failed to create so we don't delete
        self.context.helm_client.purge.assert_called_once_with(existing_group_record.helm_releases[1].name)

    @patch('kubedriver.kubegroup.group_manager.logger')
    def test_process_request_captures_internal_errors_during_processing(self, patch_logger):
        """
        Here we are testing a specific try/catch in EntityGroupManager.__process_request, which will catch errors during __process_create or __process_delete
        Note: these methods have their own error handling, which will update the Object or Helm Release record in error, so the only errors that can make it out are really bad internal errors, e.g. coding bugs

        When __process_request catches these errors it will attempt to update the request record with the failure.
        This is there to reduce the risk of the Request being left in the "IN PROGRESS" state, which ultimately leads to a hanging process and timeout in LM
        """
        group = self.__build_group_with_two_helm_releases()
        request_id = self.group_manager.create_group(self.kube_location, group)
        # Only way to get the processing to fail is to create a failure, which is caught by the handler which updates the helm record
        # If we make the logging fail as well, then error handler will create a new error, which the processing error handler (in __process_request) will catch
        self.__configure_mock_helm_install_failure(group.helm_releases[0].name)
        def side_effect(msg, *args, **kwargs):
            if msg.startswith('Create attempt of Helm Release') and msg.endswith(f'in Group \'{group.uid}\' failed'):
                raise ValueError('Mock error thrown by logger')
        patch_logger.exception.side_effect = side_effect
        self.job_queue.process_next_job()
        expected_complete_record = EntityGroupRecord('test-123',
            helm_releases=[
                HelmReleaseRecord(group.helm_releases[0].chart, group.helm_releases[0].name, group.helm_releases[0].namespace, group.helm_releases[0].values, state=EntityStates.PENDING, error=None),
                HelmReleaseRecord(group.helm_releases[1].chart, group.helm_releases[1].name, group.helm_releases[1].namespace, group.helm_releases[1].values, state=EntityStates.PENDING, error=None)
            ],
            requests=[
                RequestRecord(request_id, RequestOperations.CREATE, state=RequestStates.FAILED, error='Request encountered 1 error(s):\n\t1 - Internal error: Mock error thrown by logger')
            ]
        )
        self.assertEqual(len(self.context.record_persistence.update.call_args_list), 2)
        last_update_args, _ = self.context.record_persistence.update.call_args_list[1]
        self.assertEqual(last_update_args[0], matchers.entity_group_record(expected_complete_record))
