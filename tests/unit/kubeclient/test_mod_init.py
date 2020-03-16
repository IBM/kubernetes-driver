import unittest
import kubedriver.kubeclient as kubeclient

class TestImports(unittest.TestCase):

    def test_kube_api_controller(self):
        imported = kubeclient.KubeApiController

    def test_client_director(self):
        imported = kubeclient.KubeClientDirector

    def test_client_method_not_found_error(self):
        imported = kubeclient.ClientMethodNotFoundError

    def test_unrecognised_object_kind_error(self):
        imported = kubeclient.UnrecognisedObjectKindError

    def test_default_namespace(self):
        imported = kubeclient.DEFAULT_NAMESPACE

    def test_default_crd_api_version(self):
        imported = kubeclient.DEFAULT_CRD_API_VERSION