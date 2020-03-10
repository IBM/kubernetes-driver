import unittest
import yaml
from pathlib import Path
from kubedriver.kuberesources.resource_config_doc import ResourceConfigurationDocuments

def load_example_file(example_name):
    with open(Path(__file__).parent.joinpath('example_resource_config_files').joinpath('{0}.yaml'.format(example_name))) as f:
        content = f.read()
    return content

class TestResourceConfigurationDocuments(unittest.TestCase):

    def test_read_single_doc(self):
        file_content = load_example_file('simple')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read().resources
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].kind, 'ConfigMap')

    def test_read_multi_doc(self):
        file_content = load_example_file('multidoc')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read()
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].kind, 'ConfigMap')
        self.assertEqual(resources[1].kind, 'Ingress')
    
    def test_read_multi_doc_with_doc_separator_at_start(self):
        file_content = load_example_file('multidoc_separator_at_start')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read()
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].kind, 'ConfigMap')
        self.assertEqual(resources[1].kind, 'Ingress')

    def test_read_multi_doc_with_doc_separator_at_end(self):
        file_content = load_example_file('multidoc_separator_at_end')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read()
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].kind, 'ConfigMap')
        self.assertEqual(resources[1].kind, 'Ingress')

    def test_read_multi_doc_with_dots_at_end(self):
        file_content = load_example_file('multidoc_dots_at_end')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read()
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].kind, 'ConfigMap')
        self.assertEqual(resources[1].kind, 'Ingress')

    def test_read_multi_doc_with_emptydoc_in_middle(self):
        file_content = load_example_file('multidoc_emptydoc_in_middle')
        docs = ResourceConfigurationDocuments(file_content)
        resources = docs.read()
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].kind, 'ConfigMap')
        self.assertEqual(resources[1].kind, 'Ingress')

    def test_read_invalid_yaml(self):
        file_content = load_example_file('invalid_yaml')
        docs = ResourceConfigurationDocuments(file_content)
        with self.assertRaises(yaml.YAMLError) as context:
            resources = docs.read()