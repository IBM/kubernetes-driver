import unittest
from unittest.mock import MagicMock
import kubernetes.client as kubernetes_clients
from kubedriver.kubeclient.mod_director import (KubeModDirector, CREATE_ACTION, DELETE_ACTION, UPDATE_ACTION, READ_ACTION, GET_ACTION, LIST_ACTION)

class TestKubeModDirector(unittest.TestCase):

    def setUp(self):
        self.director = KubeModDirector()
        self.base_kube_client = MagicMock()

    def test_get_api_client_class_name_for_version_core_object(self):
        class_name = self.director.get_api_client_class_name_for_version('v1')
        self.assertEqual(class_name, 'CoreV1Api')

    def test_get_api_client_class_name_for_version_non_core_object(self):
        class_name = self.director.get_api_client_class_name_for_version('policy/v1beta1')
        self.assertEqual(class_name, 'PolicyV1beta1Api')

    def test_get_api_client_class_name_for_version_extensions_group(self):
        class_name = self.director.get_api_client_class_name_for_version('apiextensions.k8s.io/v1beta1')
        self.assertEqual(class_name, 'ApiextensionsV1beta1Api')

    def test_get_api_client_class_name_for_version_custom_object(self):
        class_name = self.director.get_api_client_class_name_for_version('stratoss.accantosystems.com/v1alpha1')
        self.assertEqual(class_name, 'CustomObjectsApi')

    def test_get_api_client_class_for_version_core_object(self):
        class_result = self.director.get_api_client_class_for_version('v1')
        self.assertEqual(class_result, kubernetes_clients.CoreV1Api)

    def test_get_api_client_class_for_version_non_core_object(self):
        class_result = self.director.get_api_client_class_for_version('policy/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.PolicyV1beta1Api)

    def test_get_api_client_class_for_version_extensions_group(self):
        class_result = self.director.get_api_client_class_for_version('apiextensions.k8s.io/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.ApiextensionsV1beta1Api)

    def test_get_api_client_class_for_version_custom_object(self):
        class_result = self.director.get_api_client_class_for_version('stratoss.accantosystems.com/v1alpha1')
        self.assertEqual(class_result, kubernetes_clients.CustomObjectsApi)

    def test_build_api_client_for_version_core_object(self):
        class_result = self.director.build_api_client_for_version('v1', self.base_kube_client)
        self.assertEqual(class_result.__class__, kubernetes_clients.CoreV1Api)

    def test_build_api_client_for_version_non_core_object(self):
        class_result = self.director.build_api_client_for_version('policy/v1beta1', self.base_kube_client)
        self.assertEqual(class_result.__class__, kubernetes_clients.PolicyV1beta1Api)

    def test_build_api_client_for_version_extensions_group(self):
        class_result = self.director.build_api_client_for_version('apiextensions.k8s.io/v1beta1', self.base_kube_client)
        self.assertEqual(class_result.__class__, kubernetes_clients.ApiextensionsV1beta1Api)

    def test_build_api_client_for_version_custom_object(self):
        class_result = self.director.build_api_client_for_version('stratoss.accantosystems.com/v1alpha1', self.base_kube_client)
        self.assertEqual(class_result.__class__, kubernetes_clients.CustomObjectsApi)

    def test_convert_kind_to_method_ready(self):
        self.assertEqual(self.director.convert_kind_to_method_ready('ConfigMap'), 'config_map')
        self.assertEqual(self.director.convert_kind_to_method_ready('Pod'), 'pod')
        self.assertEqual(self.director.convert_kind_to_method_ready('CustomResourceDefinition'), 'custom_resource_definition')

    def test_try_namespaced_method_for_create(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, CREATE_ACTION, 'Pod')
        self.assertTrue(found)
        self.assertEqual(method, api_client.create_namespaced_pod)

    def test_try_namespaced_method_for_create_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, CREATE_ACTION, 'Namespace')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_namespaced_method_for_read(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, READ_ACTION, 'Pod')
        self.assertTrue(found)
        self.assertEqual(method, api_client.read_namespaced_pod)

    def test_try_namespaced_method_for_read_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, READ_ACTION, 'Namespace')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_namespaced_method_for_update(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, UPDATE_ACTION, 'Pod')
        self.assertTrue(found)
        self.assertEqual(method, api_client.replace_namespaced_pod)

    def test_try_namespaced_method_for_update_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, UPDATE_ACTION, 'Namespace')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_namespaced_method_for_delete(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, DELETE_ACTION, 'Pod')
        self.assertTrue(found)
        self.assertEqual(method, api_client.delete_namespaced_pod)

    def test_try_namespaced_method_for_delete_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, DELETE_ACTION, 'Namespace')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_namespaced_method_for_list(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, LIST_ACTION, 'Pod')
        self.assertTrue(found)
        self.assertEqual(method, api_client.list_namespaced_pod)

    def test_try_namespaced_method_for_list_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_namespaced_method(api_client, LIST_ACTION, 'Namespace')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method_for_create(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, CREATE_ACTION, 'Namespace')
        self.assertTrue(found)
        self.assertEqual(method, api_client.create_namespace)

    def test_try_plain_method_for_create_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, CREATE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method_for_read(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, READ_ACTION, 'Namespace')
        self.assertTrue(found)
        self.assertEqual(method, api_client.read_namespace)

    def test_try_plain_method_for_read_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, READ_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method_for_update(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, UPDATE_ACTION, 'Namespace')
        self.assertTrue(found)
        self.assertEqual(method, api_client.replace_namespace)

    def test_try_plain_method_for_update_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, UPDATE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method_for_delete(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, DELETE_ACTION, 'Namespace')
        self.assertTrue(found)
        self.assertEqual(method, api_client.delete_namespace)

    def test_try_plain_method_for_delete_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, DELETE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method_for_list(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, LIST_ACTION, 'Namespace')
        self.assertTrue(found)
        self.assertEqual(method, api_client.list_namespace)

    def test_try_plain_method_for_list_not_found(self):
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        found, method = self.director.try_plain_method(api_client, LIST_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_cluster_method_for_create(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, CREATE_ACTION, 'CustomObject')
        self.assertTrue(found)
        self.assertEqual(method, api_client.create_cluster_custom_object)

    def test_try_cluster_method_for_create_not_found(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, CREATE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_cluster_method_for_get(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, GET_ACTION, 'CustomObject')
        self.assertTrue(found)
        self.assertEqual(method, api_client.get_cluster_custom_object)

    def test_try_cluster_method_for_get_not_found(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, GET_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_cluster_method_for_update(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, UPDATE_ACTION, 'CustomObject')
        self.assertTrue(found)
        self.assertEqual(method, api_client.replace_cluster_custom_object)

    def test_try_cluster_method_for_update_not_found(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, UPDATE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_cluster_method_for_delete(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, DELETE_ACTION, 'CustomObject')
        self.assertTrue(found)
        self.assertEqual(method, api_client.delete_cluster_custom_object)

    def test_try_cluster_method_for_delete_not_found(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, DELETE_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_cluster_method_for_list(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, LIST_ACTION, 'CustomObject')
        self.assertTrue(found)
        self.assertEqual(method, api_client.list_cluster_custom_object)

    def test_try_cluster_method_for_list_not_found(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        found, method = self.director.try_cluster_method(api_client, LIST_ACTION, 'Pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_is_custom_obj_api(self):
        api_client = kubernetes_clients.CustomObjectsApi(self.base_kube_client)
        self.assertTrue(self.director.is_custom_obj_api(api_client))
        api_client = kubernetes_clients.CoreV1Api(self.base_kube_client)
        self.assertFalse(self.director.is_custom_obj_api(api_client))