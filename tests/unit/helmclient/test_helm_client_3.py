import unittest
from unittest.mock import patch, MagicMock
from kubedriver.helmclient import HelmClient
from kubedriver.helmobjects import HelmReleaseDetails
from kubedriver.helmclient import HelmError
from kubedriver.helmclient import HelmCommandNotFoundError

EXAMPLE_MANIFEST = b'''
NAME: myhelmchart
LAST DEPLOYED: Fri Jul  3 13:48:31 2020
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
USER-SUPPLIED VALUES:
valueA:
  mapKeyA: mapValueA

COMPUTED VALUES:
affinity: {}
image:
  pullPolicy: IfNotPresent
tolerations: []

HOOKS:
MANIFEST:
---
# Source: mychart/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myhelm-mychart
  labels:
    app: mychart
spec:
  type: ClusterIP
---
# Source: mychart/templates/deployment.yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: myhelm-mychart
spec:
  replicas: 1

NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace default -l "app=mychart,release=myhelmchart" -o jsonpath="{.items[0].metadata.name}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl port-forward $POD_NAME 8080:80
'''

class TestHelmClient3(unittest.TestCase):
    """
        The kubernetes driver supports multiple versions of helm that have different syntax for the helm commands. This class is to test actions using the Helm 3 syntax.
    """

    def setUp(self):
        self.client = HelmClient('kubeconfig', '3.15.0')

    def tearDown(self):
        self.client.close()

    def __mock_subprocess_response(self, mock_subprocess, returncode, stdout):
        mock_subprocess.run.return_value = MagicMock(returncode=returncode, stdout=stdout)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_install(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install('chart', 'name', 'namespace')
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_install_wait(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install(chart='chart', name='name', namespace='namespace', wait=True, timeout=30)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_install_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.install, 'chart', 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_install_command_error(self, mock_subprocess):
            self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
            self.assertRaises(HelmCommandNotFoundError, self.client.install, 'chart', 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_upgrade(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.upgrade(chart='chart', name='name', namespace='namespace', wait=True, timeout=30)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_upgrade_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.upgrade, 'chart', 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_upgrade_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.upgrade, 'chart', 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_delete(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        result = self.client.delete('name', 'namespace')
        self.assertEqual(result, None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_delete_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.delete, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_delete_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.delete, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_purge(self, mock_subprocess):
        self.client = HelmClient('kubeconfig', '3.15.0')
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        result = self.client.purge('name', 'namespace')
        self.assertEqual(result, None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_purge_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.purge, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_purge_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.purge, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_safe_get(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        success, helm_release = self.client.safe_get('name', 'namespace')
        self.assertEqual(success, True)
        self.assertIsInstance(helm_release, HelmReleaseDetails)
        self.assertEqual(helm_release.revision, 1)
        self.assertEqual(helm_release.last_deployed, 'Fri Jul  3 13:48:31 2020')
        self.assertEqual(helm_release.chart, None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_safe_get_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.safe_get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_safe_get_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.safe_get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get_helm_3(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        helm_release = self.client.get('myhelm', 'default')
        self.assertIsInstance(helm_release, HelmReleaseDetails)
        self.assertEqual(helm_release.name, 'myhelm')
        self.assertEqual(helm_release.last_deployed, 'Fri Jul  3 13:48:31 2020')
        self.assertEqual(helm_release.namespace, 'default')
        self.assertEqual(helm_release.status, 'deployed')
        self.assertEqual(helm_release.revision, 1)
        self.assertEqual(helm_release.user_supplied_values, {
            'valueA': {
                'mapKeyA': 'mapValueA'
            }
        })
        self.assertEqual(helm_release.computed_values, {
            'affinity': {},
            'image': {
              'pullPolicy': 'IfNotPresent'
            },
            'tolerations': []
        })
        self.assertEqual(helm_release.manifest, [
            {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': 'myhelm-mychart',
                    'labels': {
                        'app': 'mychart',
                    }
                },
                'spec': {
                    'type': 'ClusterIP'
                }
            },
            {
              "apiVersion": "apps/v1beta2",
              "kind": "Deployment",
              "metadata": {
                "name": "myhelm-mychart"
              },
              "spec": {
                "replicas": 1
              }
            }
        ])

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_install_values(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install('chart', 'name', 'namespace', values=['valuefile_1.yaml'], setfiles=None, wait=None, timeout=None)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_upgrade_values(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install('chart', 'name', 'namespace', values=['valuefile_1.yaml'], setfiles=None, wait=None, timeout=None)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_install_values_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.install, 'chart', 'name', 'namespace', values='valueA.mapKeyA', setfiles=None, wait=None, timeout=None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_upgrade_values_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.upgrade, 'chart', 'name', 'namespace', values='valueA.mapKeyA', setfiles=None, wait=None, timeout=None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_install_setfiles(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install('chart', 'name', 'namespace', values=None, setfiles={'valueA.mapKeyA': 'mapValueB'}, wait=None, timeout=None)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_upgrade_setfiles(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        name = self.client.install('chart', 'name', 'namespace', values=None, setfiles={'valueA.mapKeyA': 'mapValueB'}, wait=None, timeout=None)
        self.assertEqual(name, 'name')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_install_setfiles_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.install, 'chart', 'name', 'namespace', values=None, setfiles=['valueA.mapKeyA', 'mapValueB'], wait=None, timeout=None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_helm_client_upgrade_setfiles_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.upgrade, 'chart', 'name', 'namespace', values=None, setfiles=['valueA.mapKeyA', 'mapValueB'], wait=None, timeout=None)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.get, 'name', 'namespace')

