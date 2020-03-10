import unittest
import kubernetes.client as kubernetes_client_mod
from unittest.mock import MagicMock
from kubedriver.kubeclient.resource_config_handler import ResourceConfigurationHandler
from kubedriver.kuberesources.resource_config import ResourceConfiguration
from kubedriver.kubeclient.exceptions import InvalidResourceConfiguration

class TestResourceConfigurationHandler(unittest.TestCase):

    def setUp(self):
        self.mock_kube_client = MagicMock()
        self.mock_api_converter = MagicMock()
        self.mock_api_client = MagicMock()
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        self.handler = ResourceConfigurationHandler(self.mock_kube_client, self.mock_api_converter)

    def test_create_resource_namespaced_object_with_no_namespace_specified(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing'
            },
            'data': {
                'dataItemA': 'A',
                'dataItemB': 'B'
            }
        })
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        self.handler.create_resource(test_resource_config)
        mock_api_method.assert_called_once_with(body=test_resource_config.resource_data, namespace='default')

    def test_create_resource_namespaced_object_with_namespace_in_metadata(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing',
                'namespace': 'DummyNamespace'
            },
            'data': {
                'dataItemA': 'A',
                'dataItemB': 'B'
            }
        })
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        self.handler.create_resource(test_resource_config)
        mock_api_method.assert_called_once_with(body=test_resource_config.resource_data, namespace='DummyNamespace')

    def test_create_resource_namespaced_object_with_no_namespace_specified_alternative_default(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing'
            },
            'data': {
                'dataItemA': 'A',
                'dataItemB': 'B'
            }
        })
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        self.handler.create_resource(test_resource_config, default_namespace='altdefault')
        mock_api_method.assert_called_once_with(body=test_resource_config.resource_data, namespace='altdefault')

    def test_create_resource_custom_namespaced_with_no_namespace_specified(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'example.com/v1alpha1',
            'kind': 'MyResource',
            'metadata': {
                'name': 'Testing'
            }
        })
        #Mocks
        self.mock_api_converter.read_api_version.return_value = ('example.com', 'v1alpha1')
        self.mock_api_client = MagicMock(__class__=kubernetes_client_mod.CustomObjectsApi)
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        self.mock_api_client.list_custom_resource_definition.return_value = [MockCrdResponse('example.com', 'v1alpha1', 'myresources')]
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        #Test
        self.handler.create_resource(test_resource_config)
        self.mock_api_client.list_custom_resource_definition.assert_called_once_with(field_selector='spec.group=example.com,spec.names.kind=MyResource')
        mock_api_method.assert_called_once_with(group='example.com', version='v1alpha1', plural='myresources', body=test_resource_config.resource_data, namespace='default')

    def test_create_resource_custom_namespaced_with_namespace_in_metadata(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'example.com/v1alpha1',
            'kind': 'MyResource',
            'metadata': {
                'name': 'Testing',
                'namespace': 'DummyNamespace'
            }
        })
        #Mocks
        self.mock_api_converter.read_api_version.return_value = ('example.com', 'v1alpha1')
        self.mock_api_client = MagicMock(__class__=kubernetes_client_mod.CustomObjectsApi)
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        self.mock_api_client.list_custom_resource_definition.return_value = [MockCrdResponse('example.com', 'v1alpha1', 'myresources')]
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        #Test
        self.handler.create_resource(test_resource_config)
        mock_api_method.assert_called_once_with(group='example.com', version='v1alpha1', plural='myresources', body=test_resource_config.resource_data, namespace='DummyNamespace')

    def test_create_resource_custom_namespaced_with_no_namespace_specified_alternative_default(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'example.com/v1alpha1',
            'kind': 'MyResource',
            'metadata': {
                'name': 'Testing'
            }
        })
        #Mocks
        self.mock_api_converter.read_api_version.return_value = ('example.com', 'v1alpha1')
        self.mock_api_client = MagicMock(__class__=kubernetes_client_mod.CustomObjectsApi)
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        self.mock_api_client.list_custom_resource_definition.return_value = [MockCrdResponse('example.com', 'v1alpha1', 'myresources')]
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        #Test
        self.handler.create_resource(test_resource_config, default_namespace='AltNamespace')
        mock_api_method.assert_called_once_with(group='example.com', version='v1alpha1', plural='myresources', body=test_resource_config.resource_data, namespace='AltNamespace')

    def test_create_resource_custom_crd_not_found_errors(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'example.com/v1alpha1',
            'kind': 'MyResource',
            'metadata': {
                'name': 'Testing'
            }
        })
        #Mocks
        self.mock_api_client = MagicMock(__class__=kubernetes_client_mod.CustomObjectsApi)
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        self.mock_api_converter.read_api_version.return_value = ('example.com', 'v1alpha1')
        self.mock_api_client.list_custom_resource_definition.return_value = []
        #Test
        with self.assertRaises(InvalidResourceConfiguration) as context:
            self.handler.create_resource(test_resource_config)  
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1alpha1\', kind \'MyResource\'')

    def test_create_resource_custom_crd_match_on_versions_list(self):
        test_resource_config = ResourceConfiguration({
            'apiVersion': 'example.com/v1alpha1',
            'kind': 'MyResource',
            'metadata': {
                'name': 'Testing'
            }
        })
        #Mocks
        self.mock_api_converter.read_api_version.return_value = ('example.com', 'v1alpha1')
        self.mock_api_client = MagicMock(__class__=kubernetes_client_mod.CustomObjectsApi)
        self.mock_api_converter.build_api_client_for.return_value = self.mock_api_client
        self.mock_api_client.list_custom_resource_definition.return_value = [
            MockCrdResponse('example.com', 'v1beta1', 'myresources', versions=[MockVersionEntry('v1alpha1')])
        ]
        mock_api_method = MagicMock()
        self.mock_api_converter.determine_api_create_method.return_value = (mock_api_method, True)
        #Test
        self.handler.create_resource(test_resource_config)
        self.mock_api_client.list_custom_resource_definition.assert_called_once_with(field_selector='spec.group=example.com,spec.names.kind=MyResource')
        mock_api_method.assert_called_once_with(group='example.com', version='v1alpha1', plural='myresources', body=test_resource_config.resource_data, namespace='default')


class MockCrdResponse:

    def __init__(self, group, version, plural, versions=[]):
        self.group = group
        self.version = version
        self.spec = MagicMock(names=MagicMock(plural=plural))
        self.versions = versions

class MockVersionEntry:

    def __init__(self, name):
        self.name = name
