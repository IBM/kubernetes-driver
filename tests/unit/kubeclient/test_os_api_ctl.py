import unittest
from unittest.mock import MagicMock, patch
from kubedriver.kubeclient.os_api_ctl import OpenshiftApiController
from kubedriver.kubeobjects.object_config import ObjectConfiguration
from kubernetes import client
        
class TestOpenshiftApiController(unittest.TestCase):

    @patch('kubedriver.kubeclient.os_api_ctl.DynamicClient')
    def setUp(self, mock_DynamicClient):
        self.base_kube_client = client.ApiClient()
        self.os_api_ctl = OpenshiftApiController(self.base_kube_client, default_namespace='default')
        
    def test_create_object(self):
        self.os_api_ctl._generate_additional_logs = MagicMock()
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
        self.os_api_ctl.create_object(object_config)
        assert self.os_api_ctl._generate_additional_logs.called

    def test_update_object(self):
        self.os_api_ctl._generate_additional_logs = MagicMock()
        object_config = ObjectConfiguration({
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'Testing'
            },
            'data': {
                'dataItemA': 'C',
                'dataItemB': 'D'
            }
        })
        self.os_api_ctl.update_object(object_config)
        assert self.os_api_ctl._generate_additional_logs.called

    def test_delete_object(self):
        self.os_api_ctl._generate_additional_logs = MagicMock()
        self.os_api_ctl.delete_object('v1', 'ConfigMap', 'Testing')
        assert self.os_api_ctl._generate_additional_logs.called

    def test_read_object(self):
        self.os_api_ctl._generate_additional_logs = MagicMock()
        self.os_api_ctl.read_object('v1', 'ConfigMap', 'Testing')
        assert self.os_api_ctl._generate_additional_logs.called