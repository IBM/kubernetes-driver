import unittest
from unittest.mock import MagicMock
from kubedriver.kubeclient.crd_director import CrdDirector
from kubedriver.kubeclient.mod_director import LIST_ACTION
from kubernetes.client.models import V1beta1CustomResourceDefinitionList
from tests.unit.utils.crd_builder import build_crd

class TestCrdDirector(unittest.TestCase):

    def setUp(self):
        self._setUp_mock_crd_client()
        self._setUp_mod_director_to_return_crd_client()
        self.base_kube_client = MagicMock()
        self.crd_director = CrdDirector(self.base_kube_client, mod_director=self.mod_director)

    def _setUp_mock_crd_client(self):
        self.crd_api_client = MagicMock()
        self.crds = []
        def list_crds():
            return V1beta1CustomResourceDefinitionList(items=self.crds)
        self.crd_api_client.list_crds.side_effect = list_crds

    def _setUp_mod_director_to_return_crd_client(self):
        self.mod_director = MagicMock()
        self.mod_director.build_api_client_for_version.return_value = self.crd_api_client
        def try_plain_method(api_client, action_type, kind):
            if action_type == LIST_ACTION:
                return True, self.crd_api_client.list_crds
            else:
                return False, None
        self.mod_director.try_plain_method.side_effect = try_plain_method
        
    def _add_crd(self, **kwargs):
        crd = build_crd(**kwargs)
        self.crds.append(crd)
        return crd


    def test_get_crd_by_kind_not_in_cache(self):
        created_crd = self._add_crd()
        crd = self.crd_director.get_crd_by_kind('example.com', 'MyCustom')
        self.assertEqual(crd, created_crd)