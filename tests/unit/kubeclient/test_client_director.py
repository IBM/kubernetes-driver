import unittest
import kubernetes.client as kubernetes_clients
from unittest.mock import MagicMock
from kubedriver.kubeclient.client_director import KubeClientDirector
from kubedriver.kubeclient.exceptions import ClientMethodNotFoundError

class TestKubeClientDirector(unittest.TestCase):

    def setUp(self):
        self.director = KubeClientDirector()
        self.base_kube_client = MagicMock()

    def test_parse_api_version_handles_core_version(self):
        group, version = self.director.parse_api_version('v1')
        self.assertEqual(group, 'core')
        self.assertEqual(version, 'v1')

    def test_parse_api_version_handles_group(self):
        group, version = self.director.parse_api_version('apiextensions.k8s.io/v1beta1')
        self.assertEqual(group, 'apiextensions.k8s.io')
        self.assertEqual(version, 'v1beta1')

    def test_determine_api_client_for_version_core_object(self):
        class_result = self.director.determine_api_client_for_version('v1')
        self.assertEqual(class_result, kubernetes_clients.CoreV1Api)

    def test_determine_api_client_for_version_non_core_object(self):
        class_result = self.director.determine_api_client_for_version('policy/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.PolicyV1beta1Api)

    def test_determine_api_client_for_version_extensions_group(self):
        class_result = self.director.determine_api_client_for_version('apiextensions.k8s.io/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.ApiextensionsV1beta1Api)

    def test_determine_api_client_for_version_custom_object(self):
        class_result = self.director.determine_api_client_for_version('stratoss.accantosystems.com/v1alpha1')
        self.assertEqual(class_result, kubernetes_clients.CustomObjectsApi)

    ##Create
    def test_determine_api_method_for_create_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.create_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_namespaced_custom_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'stratoss.accantosystems.com/v1alpha1', 'Assembly', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.create_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_create_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.create_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_create_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_create_object(self.base_kube_client, 'v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'create\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.apis.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_create_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_create_object(self.base_kube_client, 'v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.create_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Update
    def test_determine_api_method_for_update_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.replace_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_namespaced_custom_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'stratoss.accantosystems.com/v1alpha1', 'Assembly', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.replace_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_update_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.replace_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_update_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_update_object(self.base_kube_client, 'v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'replace\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.apis.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_update_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_update_object(self.base_kube_client, 'v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.replace_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Delete
    def test_determine_api_method_for_delete_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.delete_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_namespaced_custom_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'stratoss.accantosystems.com/v1alpha1', 'Assembly', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.delete_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_delete_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.delete_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_delete_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_delete_object(self.base_kube_client, 'v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'delete\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.apis.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_delete_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_delete_object(self.base_kube_client, 'v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.delete_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##Read
    def test_determine_api_method_for_read_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.read_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_namespaced_custom_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'stratoss.accantosystems.com/v1alpha1', 'Assembly', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.get_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_read_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.read_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_read_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_read_object(self.base_kube_client, 'v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'read\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.apis.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_read_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_read_object(self.base_kube_client, 'v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.read_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    ##List
    def test_determine_api_method_for_list_object_with_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'v1', 'Pod', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespaced_pod, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_non_core_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'policy/v1beta1', 'PodDisruptionBudget', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.list_namespaced_pod_disruption_budget, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_namespaced_custom_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'stratoss.accantosystems.com/v1alpha1', 'Assembly', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CustomObjectsApi)
        self.assertEqual(api_client.list_namespaced_custom_object, method)
        self.assertTrue(is_namespaced)
        self.assertTrue(is_custom_object)

    def test_determine_api_method_for_list_object_with_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'v1', 'Namespace', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespace, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_non_core_non_namespaced_object(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'policy/v1beta1', 'PodSecurityPolicy', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.PolicyV1beta1Api)
        self.assertEqual(api_client.list_pod_security_policy, method)
        self.assertFalse(is_namespaced)
        self.assertFalse(is_custom_object)

    def test_determine_api_method_for_list_object_with_object_not_found_in_api(self):
        with self.assertRaises(ClientMethodNotFoundError) as context:
            self.director.determine_api_method_for_list_object(self.base_kube_client, 'v1', 'AnUnknownResourceToThisApi', return_api_client=True)
        self.assertEqual(str(context.exception), 'Cannot determine method for action \'list\' of kind \'AnUnknownResourceToThisApi\' in Api client \'<class \'kubernetes.client.apis.core_v1_api.CoreV1Api\'>\'')

    def test_determine_api_method_for_list_object_with_camel_case_name(self):
        method, is_namespaced, is_custom_object, api_client = self.director.determine_api_method_for_list_object(self.base_kube_client, 'v1', 'ConfigMap', return_api_client=True)
        self.assertEqual(api_client.__class__, kubernetes_clients.CoreV1Api)
        self.assertEqual(api_client.list_namespaced_config_map, method)
        self.assertTrue(is_namespaced)
        self.assertFalse(is_custom_object)