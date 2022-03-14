import unittest
import yaml
from pathlib import Path
from kubedriver.kubeobjects.config_doc import ObjectConfigurationDocument

def load_example_file(example_name):
    with open(Path(__file__).parent.joinpath('example_object_config_files').joinpath('{0}.yaml'.format(example_name))) as f:
        content = f.read()
    return content

class TestObjectConfigurationDocument(unittest.TestCase):

    def test_read_single_doc(self):
        file_content = load_example_file('simple')
        docs = ObjectConfigurationDocument(file_content)
        objects = docs.read()
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].kind, 'ConfigMap')

    def test_read_invalid_yaml(self):
        file_content = load_example_file('invalid_yaml')
        docs = ObjectConfigurationDocument(file_content)
        with self.assertRaises(yaml.YAMLError) as context:
            docs.read()