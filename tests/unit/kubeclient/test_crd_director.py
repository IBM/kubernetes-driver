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
        self.crd_api_client.list_crds.assert_called_once()

    def test_get_crd_by_kind_not_found(self):
        crd = self.crd_director.get_crd_by_kind('example.com', 'MyCustom')
        self.assertIsNone(crd)
        self.crd_api_client.list_crds.assert_called_once()

    def test_get_crd_by_kind_from_cache(self):
        created_crd = self._add_crd()
        crd = self.crd_director.get_crd_by_kind('example.com', 'MyCustom')
        self.crd_api_client.list_crds.assert_called_once()
        self.crd_api_client.reset_mock()
        # Now from cache
        crd = self.crd_director.get_crd_by_kind('example.com', 'MyCustom')
        self.crd_api_client.list_crds.assert_not_called()
        self.assertEqual(crd, created_crd)

    def test_get_crd_by_kind_fills_cache(self):
        created_crdA = self._add_crd(kind='MyCustomA')   
        created_crdB = self._add_crd(kind='MyCustomB')
        first_get = self.crd_director.get_crd_by_kind('example.com', 'MyCustomA')
        self.crd_api_client.reset_mock()
        # Now from cache
        crdA = self.crd_director.get_crd_by_kind('example.com', 'MyCustomA')
        crdB = self.crd_director.get_crd_by_kind('example.com', 'MyCustomB')
        # Did not use the API, used the cache
        self.crd_api_client.list_crds.assert_not_called()

    def test_cache_limit(self):
        self.crd_director = CrdDirector(self.base_kube_client, mod_director=self.mod_director, cache_capacity=2)
        created_crdA = self._add_crd(kind='MyCustomA')   
        created_crdB = self._add_crd(kind='MyCustomB')
        created_crdC = self._add_crd(kind='MyCustomC')
        # Cache will be populated with B and C (the last 2)
        first_get = self.crd_director.get_crd_by_kind('example.com', 'MyCustomC')
        self.crd_api_client.reset_mock()
        # Get from cache
        crdB = self.crd_director.get_crd_by_kind('example.com', 'MyCustomB')
        self.crd_api_client.list_crds.assert_not_called()
        crdC = self.crd_director.get_crd_by_kind('example.com', 'MyCustomC')
        self.crd_api_client.list_crds.assert_not_called()
        # A not in cache, as B and C filled it
        crdA = self.crd_director.get_crd_by_kind('example.com', 'MyCustomA')
        self.crd_api_client.list_crds.assert_called_once()
        self.crd_api_client.reset_mock()
        # C still in cache (used later than B)
        crdC = self.crd_director.get_crd_by_kind('example.com', 'MyCustomC')
        self.crd_api_client.list_crds.assert_not_called()
        # B not in cache
        crdB = self.crd_director.get_crd_by_kind('example.com', 'MyCustomB')
        self.crd_api_client.list_crds.assert_called_once()

    def test_change_crd_api_version(self):
        # Reset as the setUp of self.crd_director will have called this
        self.mod_director.reset_mock()
        self.crd_director = CrdDirector(self.base_kube_client, mod_director=self.mod_director, crd_api_version='v1')
        self.mod_director.build_api_client_for_version.assert_called_once_with('v1', self.base_kube_client)
        crd_api_client = self.mod_director.build_api_client_for_version.return_value
        self.mod_director.try_plain_method.assert_called_once_with(crd_api_client, LIST_ACTION, 'custom_resource_definition')