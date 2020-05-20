import unittest
import kubernetes.client as kubernetes_clients
from unittest.mock import MagicMock
from kubedriver.kubeclient.mod_director import KubeModDirector
from kubedriver.kubeclient.crd_director import CrdDirector
from kubedriver.kubeclient.client_director import KubeClientDirector
from kubedriver.kubeclient.exceptions import ClientMethodNotFoundError
from tests.unit.utils.crd_builder import build_crd

class TestKubeClientDirector(unittest.TestCase):

    def setUp(self):
        self.base_kube_client = MagicMock()
        self.crd_director = MagicMock()
        self.director = KubeClientDirector(self.base_kube_client, self.crd_director)

    def _mock_namespaced_crd(self, **kwargs):
        kwargs['scope'] = 'Namespaced'
        crd = build_crd(**kwargs)
        self.crd_director.get_crd_by_kind.return_value = crd

    def _mock_cluster_crd(self, **kwargs):
        kwargs['scope'] = 'Cluster'
        crd = build_crd(**kwargs)
        self.crd_director.get_crd_by_kind.return_value = crd

    ##Create
    def test_determine_api_method_for_create_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.create_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_namespaced_custom_object(self):
        crd = self._mock_namespaced_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.create_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_create_object_with_cluster_custom_object(self):
        crd = self._mock_cluster_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.create_cluster_custom_object, method)
        self.assertFalse(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_create_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.create_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_create_object('v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'create\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.api.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_create_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object('v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Update
    def test_determine_api_method_for_update_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.replace_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_namespaced_custom_object(self):
        crd = self._mock_namespaced_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.replace_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_update_object_with_cluster_custom_object(self):
        crd = self._mock_cluster_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.replace_cluster_custom_object, method)
        self.assertFalse(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_update_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.replace_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_update_object('v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'replace\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.api.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_update_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object('v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Delete
    def test_determine_api_method_for_delete_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.delete_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_namespaced_custom_object(self):
        crd = self._mock_namespaced_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.delete_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_delete_object_with_cluster_custom_object(self):
        crd = self._mock_cluster_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.delete_cluster_custom_object, method)
        self.assertFalse(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_delete_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.delete_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_delete_object('v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'delete\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.api.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_delete_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object('v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Read
    def test_determine_api_method_for_read_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.read_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_namespaced_custom_object(self):
        crd = self._mock_namespaced_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.get_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_read_object_with_cluster_custom_object(self):
        crd = self._mock_cluster_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.get_cluster_custom_object, method)
        self.assertFalse(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_read_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.read_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_read_object('v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'read\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.api.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_read_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object('v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##List
    def test_determine_api_method_for_list_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.list_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_namespaced_custom_object(self):
        crd = self._mock_namespaced_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.list_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_list_object_with_namespaced_custom_object(self):
        crd = self._mock_cluster_crd(group='example.com', versions='v1alpha1', kind='MyCustom')
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('example.com/v1alpha1', 'MyCustom', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.list_cluster_custom_object, method)
        self.assertFalse(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_list_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.list_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_list_object('v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'list\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.api.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_list_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object('v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)