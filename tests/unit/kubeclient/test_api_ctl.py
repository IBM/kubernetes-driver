import unittest
import kubernetes.client as kubernetes_client_mod
from unittest.mock import MagicMock
from kubedriver.kubeclient.api_ctl import KubeApiController
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubedriver.kubeclient.exceptions import UnrecognisedObjectKindError
from tests.unit.utils.crd_builder import build_crd

class DeleteOptionsMatcher:

    def __eq__(self, other):
        return isinstance(other, kubernetes_client_mod.V1DeleteOptions)
        
class TestKubeApiController(unittest.TestCase):

    def setUp(self):
        self.base_kube_client = MagicMock()
        self.crd_director = MagicMock()
        self.client_director = MagicMock()
        self.api_ctl = KubeApiController(self.client_director, self.crd_director)
        self._set_up_crd_director()

    def _set_up_crd_director(self):
        self.crds = []
        def get_crd_by_kind(group, kind):
            for crd in self.crds:
                if crd.spec.group == group and crd.spec.names.kind == kind:
                    return crd
        self.crd_director.get_crd_by_kind.side_effect = get_crd_by_kind

    def __reconfigure_with_namespace(self, namespace):
        self.api_ctl = KubeApiController(self.client_director, self.crd_director, default_namespace=namespace)

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
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.data, namespace='default')
    
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
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.data, namespace='AltDefault')
    
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
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.data, namespace='AltInitDefault')

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
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('v1', 'ConfigMap')
        self.create_method.assert_called_once_with(body=object_config.data, namespace='NamespaceFromMetadata')
    
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
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('v1', 'Namespace')
        self.create_method.assert_called_once_with(body=object_config.data)
       
    def __mock_create_namespaced_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.create_method, self.create_is_namespaced, self.create_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_create_object.return_value = (self.create_method, self.create_is_namespaced, self.create_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural))

    def test_create_object_with_namespaced_custom_object(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.create_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='default')
    
    def test_create_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.create_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='AltDefault')
    
    def test_create_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.create_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='AltInitDefault')

    def test_create_object_with_namespaced_custom_object_including_namespace_metadata(self):
        self.__mock_create_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            }
        })
        self.api_ctl.create_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.create_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='NamespaceFromMetadata')

    def test_create_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_create_namespaced_custom_object(kind='MyOtherCustom')
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.create_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def __mock_create_cluster_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.create_method, self.create_is_namespaced, self.create_is_custom_object = (MagicMock(), False, True)
        self.client_director.determine_api_method_for_create_object.return_value = (self.create_method, self.create_is_namespaced, self.create_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural, scope='Cluster'))

    def test_create_object_with_cluster_custom_object(self):
        self.__mock_create_cluster_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.create_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data)

    def test_create_object_with_cluster_custom_object_plural_not_found(self):
        self.__mock_create_cluster_custom_object(kind='MyOtherCustom')
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.create_object(object_config)
        self.client_director.determine_api_method_for_create_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.create_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

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
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='default')
        self.assertEqual(result, self.read_method.return_value)

    def test_read_object_with_namespaced_object_supply_namespace_in_call(self):
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='AltNamespace')

    def test_read_object_with_namespaced_object_supply_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_read_namespaced_object()
        result = self.api_ctl.read_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('v1', 'ConfigMap')
        self.read_method.assert_called_once_with(name='Testing', namespace='AltInitNamespace')

    def __mock_read_non_namespaced_object(self):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
 
    def test_read_object_with_non_namespaced_object(self):
        self.__mock_read_non_namespaced_object()
        self.api_ctl.read_object('v1', 'Namespace', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('v1', 'Namespace')
        self.read_method.assert_called_once_with(name='Testing')
       
    def __mock_read_namespaced_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural))

    def test_read_object_with_namespaced_custom_object(self):
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.read_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='default')
    
    def test_read_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.read_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='AltNamespace')

    def test_read_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_read_namespaced_custom_object()
        self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.read_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='AltInitNamespace')

    def test_read_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_read_namespaced_custom_object(kind='MyOtherCustom')
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.read_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def __mock_read_cluster_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.read_method, self.read_is_namespaced, self.read_is_custom_object = (MagicMock(), False, True)
        self.client_director.determine_api_method_for_read_object.return_value = (self.read_method, self.read_is_namespaced, self.read_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural, scope='Cluster'))

    def test_read_object_with_cluster_custom_object(self):
        self.__mock_read_cluster_custom_object()
        self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.read_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing')

    def test_read_object_with_cluster_custom_object_plural_not_found(self):
        self.__mock_read_cluster_custom_object(kind='MyOtherCustom')
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.read_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_read_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.read_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    #Delete
    def __mock_delete_namespaced_object(self):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), True, False)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)

    def test_delete_object_namespaced(self):
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='default')

    def test_delete_object_with_namespaced_object_supply_namespace_in_call(self):
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='AltNamespace')

    def test_delete_object_with_namespaced_object_supply_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_delete_namespaced_object()
        self.api_ctl.delete_object('v1', 'ConfigMap', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('v1', 'ConfigMap')
        self.delete_method.assert_called_once_with(name='Testing', namespace='AltInitNamespace')

    def __mock_delete_non_namespaced_object(self):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), False, False)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)
 
    def test_delete_object_with_non_namespaced_object(self):
        self.__mock_delete_non_namespaced_object()
        self.api_ctl.delete_object('v1', 'Namespace', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('v1', 'Namespace')
        self.delete_method.assert_called_once_with(name='Testing')
       
    def __mock_delete_namespaced_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural))

    def test_delete_object_with_namespaced_custom_object(self):
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.delete_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='default', body=DeleteOptionsMatcher())
    
    def test_delete_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing', namespace='AltNamespace')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.delete_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='AltNamespace', body=DeleteOptionsMatcher())

    def test_delete_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitNamespace')
        self.__mock_delete_namespaced_custom_object()
        self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.delete_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', namespace='AltInitNamespace', body=DeleteOptionsMatcher())

    def test_delete_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_delete_namespaced_custom_object(kind='MyOtherCustom')
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.delete_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def test_is_object_namespaced_with_namespaced_object_returns_true(self):
        self.__mock_read_namespaced_object()
        is_namespaced = self.api_ctl.is_object_namespaced('v1', 'ConfigMap')
        self.assertTrue(is_namespaced)

    def test_is_object_namespaced_with_non_namespaced_object_returns_false(self):
        self.__mock_read_non_namespaced_object()
        is_namespaced = self.api_ctl.is_object_namespaced('v1', 'Namespace')
        self.assertFalse(is_namespaced)

    def __mock_delete_cluster_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object = (MagicMock(), False, True)
        self.client_director.determine_api_method_for_delete_object.return_value = (self.delete_method, self.delete_is_namespaced, self.delete_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural, scope='Cluster'))

    def test_delete_object_with_cluster_custom_object(self):
        self.__mock_delete_cluster_custom_object()
        self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.delete_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', name='Testing', body=DeleteOptionsMatcher())

    def test_delete_object_with_cluster_custom_object_plural_not_found(self):
        self.__mock_delete_cluster_custom_object(kind='MyOtherCustom')
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.delete_object('example.com/v1', 'MyCustom', 'Testing')
        self.client_director.determine_api_method_for_delete_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.delete_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

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
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.data, namespace='default')
    
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
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.data, namespace='AltDefault')
    
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
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.data, namespace='AltInitDefault')

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
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('v1', 'ConfigMap')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.data, namespace='NamespaceFromMetadata')
    
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
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('v1', 'Namespace')
        self.update_method.assert_called_once_with(name='Testing', body=object_config.data)

    def __mock_update_namespaced_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.update_method, self.update_is_namespaced, self.update_is_custom_object = (MagicMock(), True, True)
        self.client_director.determine_api_method_for_update_object.return_value = (self.update_method, self.update_is_namespaced, self.update_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural))

    def test_update_object_with_namespaced_custom_object(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='default')
    
    def test_update_object_with_namespaced_custom_object_supply_default_namespace_in_call(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='AltDefault')
    
    def test_update_object_with_namespaced_custom_object_supply_default_namespace_in_init(self):
        self.__reconfigure_with_namespace('AltInitDefault')
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='AltInitDefault')

    def test_update_object_with_namespaced_custom_object_including_namespace_metadata(self):
        self.__mock_update_namespaced_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing',
                'namespace': 'NamespaceFromMetadata'
            }
        })
        self.api_ctl.update_object(object_config, default_namespace='AltDefault')
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.update_method.assert_called_once_with(name='Testing', group='example.com', version='v1', plural='mycustoms', body=object_config.data, namespace='NamespaceFromMetadata')

    def test_update_object_with_namespaced_custom_object_plural_not_found(self):
        self.__mock_update_namespaced_custom_object(kind='MyOtherCustom')
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.update_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')

    def __mock_update_cluster_custom_object(self, group='example.com', kind='MyCustom', plural='mycustoms'):
        self.update_method, self.update_is_namespaced, self.update_is_custom_object = (MagicMock(), False, True)
        self.client_director.determine_api_method_for_update_object.return_value = (self.update_method, self.update_is_namespaced, self.update_is_custom_object)
        self.crds.append(build_crd(group=group, kind=kind, plural=plural, scope='Cluster'))

    def test_update_object_with_cluster_custom_object(self):
        self.__mock_update_cluster_custom_object()
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.crd_director.get_crd_by_kind.assert_called_once_with('example.com', 'MyCustom')
        self.update_method.assert_called_once_with(group='example.com', version='v1', plural='mycustoms', body=object_config.data)

    def test_update_object_with_cluster_custom_object_plural_not_found(self):
        self.__mock_update_cluster_custom_object(kind='MyOtherCustom')
        object_config = ObjectConfiguration({
            'apiVersion': 'example.com/v1',
            'kind': 'MyCustom',
            'metadata': {
                'name': 'Testing'
            }
        })
        with self.assertRaises(UnrecognisedObjectKindError) as context:
            self.api_ctl.update_object(object_config)
        self.client_director.determine_api_method_for_update_object.assert_called_once_with('example.com/v1', 'MyCustom')
        self.update_method.assert_not_called()
        self.assertEqual(str(context.exception), 'Could not find a CRD for custom Resource with group \'example.com\', version \'v1\', kind \'MyCustom\' - CRD required to determine the Resource plural')
