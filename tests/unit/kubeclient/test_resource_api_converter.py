import unittest
import kubernetes.client as kubernetes_clients
from unittest.mock import MagicMock
from kubedriver.kubeclient.resource_api_converter import ResourceApiConverter


class TestResourceApiConverter(unittest.TestCase):

    def setUp(self):
        self.converter = ResourceApiConverter()

    def test_read_api_version_handles_core_version(self):
        group, version = self.converter.read_api_version('v1')
        self.assertEqual(group, 'core')
        self.assertEqual(version, 'v1')

    def test_read_api_version_handles_group(self):
        group, version = self.converter.read_api_version('apiextensions.k8s.io/v1beta1')
        self.assertEqual(group, 'apiextensions.k8s.io')
        self.assertEqual(version, 'v1beta1')

    def test_determine_api_class_name_core_version(self):
        class_name = self.converter.determine_api_class_name('v1')
        self.assertEqual(class_name, 'CoreV1Api')

    def test_determine_api_class_name_with_group(self):
        class_name = self.converter.determine_api_class_name('batch/v1beta1')
        self.assertEqual(class_name, 'BatchV1beta1Api')

    def test_determine_api_class_name_ext_version(self):
        class_name = self.converter.determine_api_class_name('apiextensions.k8s.io/v1beta1')
        self.assertEqual(class_name, 'ApiextensionsV1beta1Api')

    def test_determine_api_class_name_ext_version_and_suffix(self):
        # Not sure if this is ever needed but making sure that the k8s.io is the only part to be removed
        class_name = self.converter.determine_api_class_name('apiextensions.k8s.io.morestuff/v1beta1')
        self.assertEqual(class_name, 'ApiextensionsMorestuffV1beta1Api')

    def test_determine_api_class_core(self):
        class_result = self.converter.determine_api_class('v1')
        self.assertEqual(class_result, kubernetes_clients.CoreV1Api)

    def test_determine_api_class_with_group(self):
        class_result = self.converter.determine_api_class('policy/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.PolicyV1beta1Api)

    def test_determine_api_class_with_ext_group(self):
        class_result = self.converter.determine_api_class('apiextensions.k8s.io/v1beta1')
        self.assertEqual(class_result, kubernetes_clients.ApiextensionsV1beta1Api)

    def test_determine_api_class_with_unrecognised_api_returns_custom_object_api(self):
        class_result = self.converter.determine_api_class('stratoss.accantosystems.com/v1alpha1')
        self.assertEqual(class_result, kubernetes_clients.CustomObjectsApi)

    def test_build_api_client_for_core(self):
        api = self.converter.build_api_client_for(MagicMock(), 'v1')
        self.assertEqual(api.__class__, kubernetes_clients.CoreV1Api)

    def test_build_api_client_for_group(self):
        api = self.converter.build_api_client_for(MagicMock(), 'policy/v1beta1')
        self.assertEqual(api.__class__, kubernetes_clients.PolicyV1beta1Api)

    def test_build_api_client_for_ext_group(self):
        api = self.converter.build_api_client_for(MagicMock(), 'apiextensions.k8s.io/v1beta1')
        self.assertEqual(api.__class__, kubernetes_clients.ApiextensionsV1beta1Api)

    def test_build_api_client_for_unrecognised_api_returns_custom_object_api(self):
        api = self.converter.build_api_client_for(MagicMock(), 'stratoss.accantosystems.com/v1alpha1')
        self.assertEqual(api.__class__, kubernetes_clients.CustomObjectsApi)

    def test_convert_kind_to_method_ready(self):
        result = self.converter.convert_kind_to_method_ready('ConfigMap')
        self.assertEqual(result, 'config_map')
        result = self.converter.convert_kind_to_method_ready('Pod')
        self.assertEqual(result, 'pod')

    def test_try_namespaced_method(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        found, method = self.converter.try_namespaced_method(core_api, 'create', 'pod')
        self.assertTrue(found)
        self.assertEqual(method, core_api.create_namespaced_pod)
        found, method = self.converter.try_namespaced_method(core_api, 'delete', 'pod')
        self.assertTrue(found)
        self.assertEqual(method, core_api.delete_namespaced_pod)
        found, method = self.converter.try_namespaced_method(core_api, 'replace', 'pod')
        self.assertTrue(found)
        self.assertEqual(method, core_api.replace_namespaced_pod)

    def test_try_namespaced_method_not_found(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        found, method = self.converter.try_namespaced_method(core_api, 'create', 'custom_resource')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_try_plain_method(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        found, method = self.converter.try_plain_method(core_api, 'create', 'namespace')
        self.assertTrue(found)
        self.assertEqual(method, core_api.create_namespace)
        found, method = self.converter.try_plain_method(core_api, 'delete', 'namespace')
        self.assertTrue(found)
        self.assertEqual(method, core_api.delete_namespace)
        found, method = self.converter.try_plain_method(core_api, 'replace', 'namespace')
        self.assertTrue(found)
        self.assertEqual(method, core_api.replace_namespace)

    def test_try_plain_method_not_found(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        found, method = self.converter.try_plain_method(core_api, 'create', 'pod')
        self.assertFalse(found)
        self.assertIsNone(method)

    def test_determine_api_method_plain(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(core_api, 'namespace', 'create')
        self.assertEqual(method, core_api.create_namespace)
        self.assertFalse(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(core_api, 'namespace', 'delete')
        self.assertEqual(method, core_api.delete_namespace)
        self.assertFalse(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(core_api, 'namespace', 'replace')
        self.assertEqual(method, core_api.replace_namespace)
        self.assertFalse(is_namespaced)

    def test_determine_api_method_namespaced(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(core_api, 'pod', 'create')
        self.assertEqual(method, core_api.create_namespaced_pod)
        self.assertTrue(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(core_api, 'config_map', 'delete')
        self.assertEqual(method, core_api.delete_namespaced_config_map)
        self.assertTrue(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(core_api, 'secret', 'replace')
        self.assertEqual(method, core_api.replace_namespaced_secret)
        self.assertTrue(is_namespaced)

    def test_determine_api_method_custom_object(self):
        api = kubernetes_clients.CustomObjectsApi(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(api, 'MyResource', 'create')
        self.assertEqual(method, api.create_namespaced_custom_object)
        self.assertTrue(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(api, 'MyResource', 'delete')
        self.assertEqual(method, api.delete_namespaced_custom_object)
        self.assertTrue(is_namespaced)
        method, is_namespaced = self.converter.determine_api_method(api, 'MyResource', 'replace')
        self.assertEqual(method, api.replace_namespaced_custom_object)
        self.assertTrue(is_namespaced)

    def test_determine_api_create_method(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(core_api, 'pod', 'create')
        self.assertEqual(method, core_api.create_namespaced_pod)
        self.assertTrue(is_namespaced)

    def test_determine_api_delete_method(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(core_api, 'pod', 'delete')
        self.assertEqual(method, core_api.delete_namespaced_pod)
        self.assertTrue(is_namespaced)

    def test_determine_api_replace_method(self):
        core_api = kubernetes_clients.CoreV1Api(MagicMock())
        method, is_namespaced = self.converter.determine_api_method(core_api, 'pod', 'replace')
        self.assertEqual(method, core_api.replace_namespaced_pod)
        self.assertTrue(is_namespaced)
