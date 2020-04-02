import unittest
import kubedriver.helmclient as helmclient

class TestImports(unittest.TestCase):

    def test_helm_client(self):
        imported = helmclient.HelmClient 

    def test_helm_error(self):
        imported = helmclient.HelmError