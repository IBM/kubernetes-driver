import unittest
import yaml
from pathlib import Path
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeobjects.exceptions import InvalidObjectConfigurationError

def load_yaml(example_name):
    with open(Path(__file__).parent.joinpath('example_object_config_files').joinpath('{0}.yaml'.format(example_name))) as f:
        content = f.read()
    return yaml.safe_load(content)

class TestObjectConfiguration(unittest.TestCase):

    def test_init_valid(self):
        conf = load_yaml('simple')
        object_configuration = ObjectConfiguration(conf)
        self.assertEqual(object_configuration.config, conf)
        self.assertEqual(object_configuration.api_version, 'v1')
        self.assertEqual(object_configuration.kind, 'ConfigMap')
        self.assertEqual(object_configuration.name, 'testing')

    def __check_raises_error(self, conf, expected_reason):
        with self.assertRaises(InvalidObjectConfigurationError) as context:
            ObjectConfiguration(conf)
        self.assertEqual(context.exception.reason, expected_reason)

    def test_init_missing_api_version_error(self):
        conf = load_yaml('missing_api_version')
        self.__check_raises_error(conf, 'Missing \'apiVersion\' field')

    def test_init_missing_kind_error(self):
        conf = load_yaml('missing_kind')
        self.__check_raises_error(conf, 'Missing \'kind\' field')

    def test_init_missing_metadata_error(self):
        conf = load_yaml('missing_metadata')
        self.__check_raises_error(conf, 'Missing \'metadata\' field')

    def test_init_missing_name_error(self):
        conf = load_yaml('missing_name')
        self.__check_raises_error(conf, 'Missing \'name\' field in \'metadata\'')

    