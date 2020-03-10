import unittest
import yaml
from pathlib import Path
from kubedriver.kuberesources.resource_config import ResourceConfiguration
from kubedriver.kuberesources.exceptions import InvalidResourceConfigurationError

def load_yaml(example_name):
    with open(Path(__file__).parent.joinpath('example_resource_config_files').joinpath('{0}.yaml'.format(example_name))) as f:
        content = f.read()
    return yaml.safe_load(content)

class TestResourceConfiguration(unittest.TestCase):

    def test_init_valid(self):
        resource_data = load_yaml('simple')
        resource_configuration = ResourceConfiguration(resource_data)
        self.assertEqual(resource_configuration.resource_data, resource_data)
        self.assertEqual(resource_configuration.api_version, 'v1')
        self.assertEqual(resource_configuration.kind, 'ConfigMap')
        self.assertEqual(resource_configuration.name, 'testing')

    def __check_raises_error(self, resource_data, expected_reason):
        with self.assertRaises(InvalidResourceConfigurationError) as context:
            ResourceConfiguration(resource_data)
        self.assertEqual(context.exception.reason, expected_reason)

    def test_init_missing_api_version_error(self):
        resource_data = load_yaml('missing_api_version')
        self.__check_raises_error(resource_data, 'Missing \'apiVersion\' field')

    def test_init_missing_kind_error(self):
        resource_data = load_yaml('missing_kind')
        self.__check_raises_error(resource_data, 'Missing \'kind\' field')

    def test_init_missing_metadata_error(self):
        resource_data = load_yaml('missing_metadata')
        self.__check_raises_error(resource_data, 'Missing \'metadata\' field')

    def test_init_missing_name_error(self):
        resource_data = load_yaml('missing_name')
        self.__check_raises_error(resource_data, 'Missing \'name\' field in \'metadata\'')

    