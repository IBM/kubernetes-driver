import unittest
import os
from unittest.mock import MagicMock
from ignition.service.templating import Jinja2TemplatingService
from kubedriver.resourcedriver import ExtendedResourceTemplateContext, NameManager
from kubedriver.kegd.manager import KegdStrategyLocationManager
from kubedriver.kegd.properties import KegDeploymentProperties
from kubedriver.kegd.strategy_files import KegDeploymentStrategyFiles
import kubedriver.kegd.model as kegd_model
import tests.unit.kegd.test_kegd_files as test_kegd_files
import inspect

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

def generate_render_context():
    system_properties = {
        'resourceId': '123',
        'resourceName': 'just-testing',
    }
    resource_properties = {
        'propertyA': 'A property'
    }
    request_properties = {}
    deployment_location = {}
    return render_context_builder.build(system_properties, resource_properties, request_properties, deployment_location)

def build_expected_report(**kwargs):
    return kegd_model.V1alpha1KegdStrategyReportStatus(**kwargs)

def build_expected_report_labels(keg_name):
    return {
        kegd_model.Labels.MANAGED_BY: kegd_model.LabelValues.MANAGED_BY,
        kegd_model.Labels.KEG: keg_name
    }

class TestKegdStrategyLocationManager(unittest.TestCase):

    def setUp(self):
        self.kube_location = MagicMock()
        self.templating = Jinja2TemplatingService()
        self.keg_persister = MagicMock()
        self.kegd_persister = MagicMock()
        self.api_ctl = MagicMock()
        self.context = MagicMock(kube_location=self.kube_location, keg_persister=self.keg_persister, kegd_persister=self.kegd_persister, api_ctl=self.api_ctl)
        self.worker = KegdStrategyLocationManager(self.context, self.templating)

    def test_build_process_strategy_job_has_context_data(self):
        render_context = generate_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('simple-deploy-objects')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        operation_name = 'Create'
        job = self.worker.build_process_strategy_job(keg_name, kegd_strategy, operation_name, kegd_files, render_context)
        self.assertIsNotNone(job.request_id)
        self.assertTrue(job.request_id.startswith('kegdr-'))
        self.assertEqual(job.kube_location, self.kube_location)
        self.assertEqual(job.keg_name, keg_name)

    def test_build_process_strategy_job_creates_report(self):
        render_context = generate_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('simple-deploy-objects')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        operation_name = 'Create'
        job = self.worker.build_process_strategy_job(keg_name, kegd_strategy, operation_name, kegd_files, render_context)
        expected_report = build_expected_report(
            uid=job.request_id,
            keg_name=keg_name,
            operation=operation_name,
            task_groups=[operation_name],
            run_cleanup=False,
            state=kegd_model.StrategyExecutionStates.PENDING,
            error=None
        )
        expected_labels = build_expected_report_labels(keg_name)
        self.kegd_persister.create.assert_called_once_with(job.request_id, expected_report, labels=expected_labels)
        
    def test_build_process_strategy_job_builds_script_to_deploy_objects(self):
        render_context = generate_render_context()
        keg_name = render_context['system_properties']['resourceName']
        kegd_files = get_kegd_files('simple-deploy-objects')
        kegd_strategy = parse_strategy(kegd_files.get_strategy_file())
        operation_name = 'Create'
        job = self.worker.build_process_strategy_job(keg_name, kegd_strategy, operation_name, kegd_files, render_context)
        self.assertIsNotNone(job.strategy_execution)
        strategy_execution = job.strategy_execution
        self.assertEqual(strategy_execution.operation_name, 'Create')
        self.assertEqual(strategy_execution.run_cleanup, False)
        self.assertEqual(len(strategy_execution.task_groups), 1)
        task_group = strategy_execution.task_groups[0]
        self.assertEqual(task_group.name, 'Create')
        self.assertEqual(task_group.removal_tasks, [])
        self.assertEqual(len(task_group.deploy_tasks), 1)
        