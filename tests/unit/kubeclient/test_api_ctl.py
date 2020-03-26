import unittest
import kubernetes.client as kubernetes_client_mod
from unittest.mock import MagicMock
from kubedriver.kubeclient.api_ctl import KubeApiController
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeclient.exceptions import UnrecognisedObjectKindError

class DeleteOptionsMatcher:

    def __eq__(self, other):
        return isinstance(other, kubernetes_client_mod.V1DeleteOptions)
        
class TestKubeClientGateway(unittest.TestCase):

    def setUp(self):
        self.base_kube_client = MagicMock()
        self.client_director = MagicMock()
        self.api_ctl = KubeApiController(self.base_kube_client, self.client_director)

    def __reconfigure_with_namespace(self, namespace):
        self.api_ctl = KubeApiController(self.base_kube_client, self.client_director, default_namespace=namespace)

    #Create
    def __mock_create_namespaced_object(self):
        self.create_method, self.create_is_namespaced, self.create_is_custom_object = (MagicMock(), True, False)
        self.client_director.determine_api_method_for_create_object.return_value = (self.create_method, self.create_is_namespaced, self.create_is_custom_object)
 
    def test_create_object_with_namespaced_object(self):
        self.__mock_create_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.config, namespace='default')
    
    def test_create_object_with_namespaced_object_supply_default_namespace_in_call(self):
        self.__mock_create_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.config, namespace='AltDefault')
    
    def test_create_object_with_namespaced_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_create_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.config, namespace='AltInitDefault')

    def test_create_object_with_namespaced_object_including_namespace_metadata(self):
        self.__mock_create_namespaced_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            },
            'data': {
                'dataItemA': 'A',
                'dataItemB': 'B'
            }
        })
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.config, namespace='NamespaceFromMetadata')
    
    def __mock_create_non_namespaced_object(self):
        self.create_method, self.create_is_namespaced, self.create_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_create_object.return_value = (self.create_method, self.create_is_namespaced, self.create_is_custom_object)
    
    def test_create_object_with_non_namespaced_object(self):
        self.__mock_create_non_namespaced_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'v1', 'Namespace')
        self.create_method.assert_called_once_with(body=object_config.config)
       
    def __mock_create_namespaced_custom_object(self, mock_group='customstuff', mock_version='v1alpha1', mock_plural='mycustoms'):
        self.create_method, self.create_is_namespaced, self.create_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_create_object.return_value = (self.create_method, self.create_is_namespaced, self.create_is_custom_object)
        self.list_method, self.list_is_namespaced, self.list_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_list_object.return_value = (self.list_method, self.list_is_namespaced, self.list_is_custom_object)
        self.list_method.return_value = [MockCrdResponse(mock_group, mock_version, mock_plural)]
        self.client_director.parse_api_version.return_value = (mock_group, mock_version)

    def test_create_object_with_namespaced_custom_object(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.list_method.assert_called_once_with(field_selector='spec.group=customstuff,spec.names.kind=MyCustom')
        self.create_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='default')
    
    def test_create_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.create_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='AltDefault')
    
    def test_create_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.create_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='AltInitDefault')

    def test_create_object_with_namespaced_custom_object_including_namespace_metadata(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            }
        })
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.create_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='NamespaceFromMetadata')

    def test_create_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_create_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms')]
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.create_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'customstuff\', version \'v1alpha1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def test_create_object_with_namespaced_custom_object_plural_found_on_version_list_match(self):
        self.__mock_create_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms', versions=[MockVersionEntry('v1alpha1')])]
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.create_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='default')

    #Read
    def __mock_read_namespaced_object(self):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), True, False)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
    
    def test_read_object_returns_value(self):
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing')
        self.assertEqual(result, self.read_method.return_value)

    def test_read_object_namespaced(self):
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='default')
        self.assertEqual(result, self.read_method.return_value)

    def test_read_object_with_namespaced_object_supply_namespace_in_call(self):
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='AltNamespace')

    def test_read_object_with_namespaced_object_supply_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='AltInitNamespace')

    def __mock_read_non_namespaced_object(self):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
 
    def test_read_object_with_non_namespaced_object(self):
        self.__mock_read_non_namespaced_object()
        self.api_ctl.read_object('v1', 'Namespace', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'v1', 'Namespace')
        self.read_method.assert_called_once_with(name='Testing')
       
    def __mock_read_namespaced_custom_object(self, mock_group='customstuff', mock_version='v1alpha1', mock_plural='mycustoms'):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
        self.list_method, self.list_is_namespaced, self.list_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_list_object.return_value = (self.list_method, self.list_is_namespaced, self.list_is_custom_object)
        self.list_method.return_value = [MockCrdResponse(mock_group, mock_version, mock_plural)]
        self.client_director.parse_api_version.return_value = (mock_group, mock_version)

    def test_read_object_with_namespaced_custom_object(self):
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.list_method.assert_called_once_with(field_selector='spec.group=customstuff,spec.names.kind=MyCustom')
        self.read_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='default')
    
    def test_read_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('customstuff/v1alpha1', 'MyCustom', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.read_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='AltNamespace')

    def test_read_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.read_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='AltInitNamespace')

    def test_read_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_read_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms')]
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.read_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.read_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'customstuff\', version \'v1alpha1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def test_read_object_with_namespaced_custom_object_plural_found_on_version_list_match(self):
        self.__mock_read_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms', versions=[MockVersionEntry('v1alpha1')])]
        self.api_ctl.read_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.read_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='default')

    #Delete
    def __mock_delete_namespaced_object(self):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), True, False)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)

    def test_delete_object_namespaced(self):
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='default')

    def test_delete_object_with_namespaced_object_supply_namespace_in_call(self):
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='AltNamespace')

    def test_delete_object_with_namespaced_object_supply_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='AltInitNamespace')

    def __mock_delete_non_namespaced_object(self):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)
 
    def test_delete_object_with_non_namespaced_object(self):
        self.__mock_delete_non_namespaced_object()
        self.api_ctl.delete_object('v1', 'Namespace', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'v1', 'Namespace')
        self.delete_method.assert_called_once_with(name='Testing')
       
    def __mock_delete_namespaced_custom_object(self, mock_group='customstuff', mock_version='v1alpha1', mock_plural='mycustoms'):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)
        self.list_method, self.list_is_namespaced, self.list_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_list_object.return_value = (self.list_method, self.list_is_namespaced, self.list_is_custom_object)
        self.list_method.return_value = [MockCrdResponse(mock_group, mock_version, mock_plural)]
        self.client_director.parse_api_version.return_value = (mock_group, mock_version)

    def test_delete_object_with_namespaced_custom_object(self):
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.list_method.assert_called_once_with(field_selector='spec.group=customstuff,spec.names.kind=MyCustom')
        self.delete_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='default', body=DeleteOptionsMatcher())
    
    def test_delete_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('customstuff/v1alpha1', 'MyCustom', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.delete_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='AltNamespace', body=DeleteOptionsMatcher())

    def test_delete_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.delete_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='AltInitNamespace', body=DeleteOptionsMatcher())

    def test_delete_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_delete_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms')]
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.delete_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.delete_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'customstuff\', version \'v1alpha1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def test_delete_object_with_namespaced_custom_object_plural_found_on_version_list_match(self):
        self.__mock_delete_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms', versions=[MockVersionEntry('v1alpha1')])]
        self.api_ctl.delete_object('customstuff/v1alpha1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.delete_method.assert_called_once_with(group='customstuff', version='v1alpha1', plural='mycustoms', name='Testing', namespace='default', body=DeleteOptionsMatcher())

    def test_is_object_namespaced_with_namespaced_object_returns_true(self):
        self.__mock_read_namespaced_object()
        is_namespaced = self.api_ctl.is_object_namespaced('v1', 'ConfigMap')
        self.assertTrue(is_namespaced)

    def test_is_object_namespaced_with_non_namespaced_object_returns_false(self):
        self.__mock_read_non_namespaced_object()
        is_namespaced = self.api_ctl.is_object_namespaced('v1', 'Namespace')
        self.assertFalse(is_namespaced)

    #Update
    def __mock_update_namespaced_object(self):
        self.update_method, self.update_is_namespaced, self.update_is_custom_object = (MagicMock(), True, False)
        self.client_director.determine_api_method_for_update_object.return_value = (self.update_method, self.update_is_namespaced, self.update_is_custom_object)
 
    def test_update_object_with_namespaced_object(self):
        self.__mock_update_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.config, namespace='default')
    
    def test_update_object_with_namespaced_object_supply_default_namespace_in_call(self):
        self.__mock_update_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.config, namespace='AltDefault')
    
    def test_update_object_with_namespaced_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_update_namespaced_object()
        object_config = ObjectConfiguration({
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
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.config, namespace='AltInitDefault')

    def test_update_object_with_namespaced_object_including_namespace_metadata(self):
        self.__mock_update_namespaced_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            },
            'data': {
                'dataItemA': 'A',
                'dataItemB': 'B'
            }
        })
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.config, namespace='NamespaceFromMetadata')
    
    def __mock_update_non_namespaced_object(self):
        self.update_method, self.update_is_namespaced, self.update_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_update_object.return_value = (self.update_method, self.update_is_namespaced, self.update_is_custom_object)
    
    def test_update_object_with_non_namespaced_object(self):
        self.__mock_update_non_namespaced_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'v1', 'Namespace')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.config)
       
    def __mock_update_namespaced_custom_object(self, mock_group='customstuff', mock_version='v1alpha1', mock_plural='mycustoms'):
        self.update_method, self.update_is_namespaced, self.update_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_update_object.return_value = (self.update_method, self.update_is_namespaced, self.update_is_custom_object)
        self.list_method, self.list_is_namespaced, self.list_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_list_object.return_value = (self.list_method, self.list_is_namespaced, self.list_is_custom_object)
        self.list_method.return_value = [MockCrdResponse(mock_group, mock_version, mock_plural)]
        self.client_director.parse_api_version.return_value = (mock_group, mock_version)

    def test_update_object_with_namespaced_custom_object(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.list_method.assert_called_once_with(field_selector='spec.group=customstuff,spec.names.kind=MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='default')
    
    def test_update_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='AltDefault')
    
    def test_update_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='AltInitDefault')

    def test_update_object_with_namespaced_custom_object_including_namespace_metadata(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            }
        })
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='NamespaceFromMetadata')

    def test_update_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_update_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms')]
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.update_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'customstuff\', version \'v1alpha1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def test_update_object_with_namespaced_custom_object_plural_found_on_version_list_match(self):
        self.__mock_update_namespaced_custom_object()
        self.list_method.return_value = [MockCrdResponse('customstuff', 'someotherversion', 'mycustoms', versions=[MockVersionEntry('v1alpha1')])]
        object_config = ObjectConfiguration({
            'apiVersion': 'customstuff/v1alpha1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with(self.base_kube_client, 'customstuff/v1alpha1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='customstuff', version='v1alpha1', plural='mycustoms', body=object_config.config, namespace='default')

class MockCrdResponse:

    def __init__(self, group, version, plural, versions=[]):
        self.group = group
        self.version = version
        self.spec = MagicMock(names=MagicMock(plural=plural))
        self.versions = versions

class MockVersionEntry:

    def __init__(self, name):
        self.name = name
