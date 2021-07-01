import unittest
import os
import kubedriver.kegd.model as kegd_model
import tests.unit.kegd.test_kegd_files as test_kegd_files
import inspect
import tests.utils as testutils
import time
from unittest.mock import MagicMock
from ignition.service.templating import Jinja2TemplatingService
from kubedriver.resourcedriver import ExtendedResourceTemplateContext, NameManager
from kubedriver.kegd.manager import KegdStrategyLocationManager
from kubedriver.kegd.processor import KegdStrategyLocationProcessor
from kubedriver.kegd.properties import KegDeploymentProperties
from kubedriver.kegd.strategy_files import KegDeploymentStrategyFiles
from kubedriver.kegd.jobs import ProcessStrategyJob
from kubedriver.kegd.model.strategy_execution import StrategyExecution, TaskGroup


test_kegd_files_path = os.path.dirname(inspect.getfile(test_kegd_files))

def get_kegd_files(name):
    path = os.path.join(test_kegd_files_path, name)
    if not os.path.exists(path):
        raise ValueError(f'Path does not exists: {path}')
    return KegDeploymentStrategyFiles(os.path.join(test_kegd_files_path, name))

strategy_reader = kegd_model.DeploymentStrategyFileReader(
    KegDeploymentProperties(),
    None,
    kegd_model.DeploymentStrategyParser()
)

def parse_strategy(strategy_file):
    return strategy_reader.read(strategy_file, {})

render_context_builder = ExtendedResourceTemplateContext(NameManager())

def generate_base_render_context():
    system_properties = {
        'resourceId': '123',
        'resourceName': 'just-testing',
    }
    resource_properties = {
        'propertyA': 'A property',
        'propertyB': 123
    }
    request_properties = {}
    deployment_location = {}
    return render_context_builder.build(system_properties, resource_properties, request_properties, deployment_location)

class TestKegdStrategyLocationProcessor(unittest.TestCase):

    def setUp(self):
        self.kube_location = MagicMock(default_object_namespace='default', driver_namespace='driver')
        self.templating = Jinja2TemplatingService()
        self.keg_persister = testutils.mem_persistence_mock.create()
        self.kegd_persister = testutils.mem_persistence_mock.create()
        self.api_ctl = MagicMock()
        self.context = MagicMock(kube_location=self.kube_location, keg_persister=self.keg_persister, kegd_persister=self.kegd_persister, api_ctl=self.api_ctl)
        self.processor = KegdStrategyLocationProcessor(self.context, self.templating)
        self.manager = KegdStrategyLocationManager(KegDeploymentProperties(), self.context, self.templating)

    def test_immediate_cleanup_on_retry_timeout_failure(self):
        render_context = generate_base_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('immediate-cleanup-on-ready-timeout')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy, 
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )

        # Configure Mocks
        resource_subdomain = render_context['system_properties']['resource_subdomain']
        mock_obj = MagicMock()
        mock_obj.to_dict.return_value = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{resource_subdomain}-a'
            },
            'data': {}
        }
        self.api_ctl.safe_read_object.return_value = (True, mock_obj)

        # Run
        finished = self.processor.handle_process_strategy_job(job)
        # Not Ready
        self.assertFalse(finished)

        # Wait for timeout
        time.sleep(0.2)

        # Run again
        finished = self.processor.handle_process_strategy_job(job)
        self.assertTrue(finished) 

        self.assertTrue(len(self.kegd_persister.update.call_args_list)>0)
        before_end_calls = self.kegd_persister.update.call_args_list[-3]
        self.assertEqual(before_end_calls[0][1].phase, 'Immediate cleanup on failure')

        # Confirm cleanup of object took place
        self.api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'just-testing-123-a', namespace='default')

    def test_immediate_cleanup_on_retry_attempts_exceeded(self):
        render_context = generate_base_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('immediate-cleanup-on-ready-attempts-exceeded')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy, 
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )

        # Configure Mocks
        resource_subdomain = render_context['system_properties']['resource_subdomain']
        mock_obj = MagicMock()
        mock_obj.to_dict.return_value = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{resource_subdomain}-a'
            },
            'data': {}
        }
        self.api_ctl.safe_read_object.return_value = (True, mock_obj)

        # Run #1
        finished = self.processor.handle_process_strategy_job(job)
        # Not Ready
        self.assertFalse(finished)
    
        # Run #2
        finished = self.processor.handle_process_strategy_job(job)
        # Not Ready
        self.assertFalse(finished)

        # Run #3
        finished = self.processor.handle_process_strategy_job(job)
        self.assertTrue(finished)

        self.assertTrue(len(self.kegd_persister.update.call_args_list)>0)
        before_end_calls = self.kegd_persister.update.call_args_list[-3]
        self.assertEqual(before_end_calls[0][1].phase, 'Immediate cleanup on failure')

        # Confirm cleanup of object took place
        self.api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'just-testing-123-a', namespace='default')

    def test_immediate_cleanup_with_templated_ready(self):
        render_context = generate_base_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('immediate-cleanup-with-templated-ready-script')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy,
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )

        # Configure Mocks
        resource_subdomain = render_context['system_properties']['resource_subdomain']
        mock_obj = MagicMock()
        mock_obj.to_dict.return_value = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{resource_subdomain}-a'
            },
            'data': {}
        }
        self.api_ctl.safe_read_object.return_value = (True, mock_obj)

        # Run
        finished = self.processor.handle_process_strategy_job(job)
        # Not Ready
        self.assertFalse(finished)

        # Wait for timeout
        time.sleep(0.2)

        # Run again
        finished = self.processor.handle_process_strategy_job(job)
        self.assertTrue(finished) 

        self.assertTrue(len(self.kegd_persister.update.call_args_list)>0)
        before_end_calls = self.kegd_persister.update.call_args_list[-3]
        self.assertEqual(before_end_calls[0][1].phase, 'Immediate cleanup on failure')

        # Confirm cleanup of object took place
        self.api_ctl.delete_object.assert_called_once_with('v1', 'ConfigMap', 'just-testing-123-a', namespace='default')

    def test_deploy_object(self):
        render_context = generate_base_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('simple-deploy-objects')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy, 
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )
        self.processor.handle_process_strategy_job(job)
        # Check Keg created
        keg_status = self.keg_persister.get(keg_name)
        self.assertEqual(len(keg_status.composition.objects), 1)
        object_status = keg_status.composition.objects[0]
        self.assertEqual(object_status.group, 'v1')
        self.assertEqual(object_status.kind, 'ConfigMap')
        self.assertEqual(object_status.namespace, 'default')
        self.assertEqual(object_status.name, render_context['system_properties']['resource_subdomain'] + '-a')
        self.assertEqual(object_status.uid, self.api_ctl.create_object.return_value.metadata.uid)
        self.assertEqual(object_status.state, 'Created')
        self.assertEqual(object_status.error, None)
        self.assertEqual(object_status.tags, {
            'DeployedOn': ['Create']
        })
        # Check Kegd
        kegd_status = self.kegd_persister.get(job.request_id)
        self.assertEqual(kegd_status.uid, job.request_id)
        self.assertEqual(kegd_status.keg_name, keg_name)
        self.assertEqual(kegd_status.operation, 'Create')
        self.assertEqual(kegd_status.run_cleanup, False)
        self.assertEqual(kegd_status.task_groups, ['Create'])
        self.assertEqual(kegd_status.state, 'Complete')
        self.assertEqual(kegd_status.phase, 'End')
        self.assertEqual(kegd_status.errors, [])
        self.assertEqual(kegd_status.outputs, None)
        # Check object created
        self.api_ctl.create_object.assert_called_once_with(
            ObjectConfigurationMatcher({
                'apiVersion': 'v1', 
                'kind': 'ConfigMap', 
                'metadata': {
                    'name': 'just-testing-123-a', 
                    'labels': {
                        'app.kubernetes.io/managed-by': 'kubedriver.alm', 
                        'keg.kubedriver.alm/keg': 'just-testing'
                    }
                }, 
                'data': {
                    'propertyA': 'A property', 
                    'propertyB': 'Include a number - 123'
                }
            })
        )
    
    def test_property_inputs_to_scripts(self):
        render_context = generate_base_render_context()
        render_context['string_input'] = 'A string input'
        render_context['integer_input'] = 27
        render_context['float_input'] = 2.7
        render_context['boolean_input'] = False
        render_context['timestamp_input'] = '2020-11-24T11:49:33.305403Z'
        render_context['map_input'] = {'A': 'ValueA', 'B': 2}
        render_context['list_input'] = ['A', 'B']
        render_context['custom_input'] = {'name': 'Testing', 'age': 42}
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('check-inputs')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy, 
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )
        self.api_ctl.safe_read_object.return_value = (True, MockObject({}))
        self.processor.handle_process_strategy_job(job)
        # Check Kegd
        kegd_status = self.kegd_persister.get(job.request_id)
        self.assertEqual(kegd_status.outputs, {
            'string': 'A string input',
            'integer': 27,
            'float': 2.7,
            'boolean': False,
            'timestamp': '2020-11-24T11:49:33.305403Z',
            'map': {'A': 'ValueA', 'B': 2},
            'map_A': 'ValueA',
            'map_B': 2,
            'list': ['A', 'B'],
            'list_0': 'A',
            'list_1': 'B',
            'custom': {'name': 'Testing', 'age': 42}
        })

    
    def test_return_outputs(self):
        render_context = generate_base_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('return-outputs')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        job = self.manager.build_process_strategy_job(
            keg_name=keg_name,
            kegd_strategy=kegd_strategy, 
            operation_name='Create',
            kegd_files=kegd_files,
            render_context=render_context
        )
        self.api_ctl.safe_read_object.return_value = (True, MockObject({}))
        self.processor.handle_process_strategy_job(job)
        # Check Kegd
        kegd_status = self.kegd_persister.get(job.request_id)
        self.assertEqual(kegd_status.outputs, {
            'string': 'A string',
            'integer': 123,
            'float': 1.23,
            'boolean': True,
            'timestamp': '2020-11-24T11:49:33.305403Z',
            'map': {'A': 1, 'B': 2},
            'list': ['A', 'B'],
            'custom': {'name': 'Testing', 'age': 42}
        })

class MockObject:

    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data

class ObjectConfigurationMatcher:

    def __init__(self, expected_data):
        self.expected_data = expected_data

    def __eq__(self, other):
        return other.data == self.expected_data

    def __str__(self):
        return str(self.expected_data)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expected_data!r})'
