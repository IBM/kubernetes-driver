import unittest
import os
from unittest.mock import patch
from kubedriver.kubeclient.deployment_location import KubernetesDeploymentLocation

EXAMPLE_CONFIG = {
                    'apiVersion': 'v1',
                    'clusters': [
                        {'cluster': {'server': 'localhost'}, 'name': 'kubernetes'}
                    ],
                    'contexts': [
                        {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetes' }
                    ],
                    'current-context': 'kubernetes-admin@kubernetes',
                    'kind': 'Config',
                    'preferences': {},
                    'users': [
                        {'name': 'kubernetes-admin', 'user': {}}
                    ]
                }

class TestKubernetesDeploymentLocation(unittest.TestCase):

    def test_from_dict(self):
        dl_dict = {
            'name': 'TestKube',
            'properties': {
                'client_config': EXAMPLE_CONFIG
            }
        }
        location = KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(location.name, 'TestKube')
        self.assertEqual(location.client_config, EXAMPLE_CONFIG)

    def test_from_dict_camel_case_config(self):
        dl_dict = {
            'name': 'TestKube',
            'properties': {
                'clientConfig': EXAMPLE_CONFIG
            }
        }
        location = KubernetesDeploymentLocation.from_dict(dl_dict)
        self.assertEqual(location.name, 'TestKube')
        self.assertEqual(location.client_config, EXAMPLE_CONFIG)

    @patch('kubedriver.kubeclient.deployment_location.kubeconfig')
    def test_build_client(self, mock_kube_config):
        location = KubernetesDeploymentLocation('TestKube', EXAMPLE_CONFIG)
        client = location.build_client()
        self.assertEqual(client, mock_kube_config.new_client_from_config.return_value)
        new_client_args_list = mock_kube_config.new_client_from_config.call_args_list
        self.assertEqual(len(new_client_args_list), 1)
        single_call = new_client_args_list[0]
        single_call_args = single_call[0]
        self.assertEqual(len(single_call_args), 1)
        file_path = single_call_args[0]
        self.assertFalse(os.path.exists(file_path))
        single_call_kwargs = single_call[1]
        self.assertEqual(single_call_kwargs, {'persist_config': False})
