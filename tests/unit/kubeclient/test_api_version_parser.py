import unittest
from kubedriver.kubeclient.api_version_parser import ApiVersionParser

class TestApiVersionParser(unittest.TestCase):

    def setUp(self):
        self.parser = ApiVersionParser()

    def test_parse_handles_core_version(self):
        group, version = self.parser.parse('v1')
        self.assertEqual(group, 'core')
        self.assertEqual(version, 'v1')

    def test_parse_handles_group(self):
        group, version = self.parser.parse('apiextensions.k8s.io/v1beta1')
        self.assertEqual(group, 'apiextensions.k8s.io')
        self.assertEqual(version, 'v1beta1')
