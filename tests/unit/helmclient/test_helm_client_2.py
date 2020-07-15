import unittest
from unittest.mock import patch, MagicMock
from kubedriver.helmclient import HelmClient
from kubedriver.helmobjects import HelmReleaseDetails
from kubedriver.helmclient import HelmError
from kubedriver.helmclient import HelmCommandNotFoundError

EXAMPLE_MANIFEST = b'''
REVISION: 1
RELEASED: Wed May 13 13:03:30 2020
CHART: example-chart-0.9.0
USER-SUPPLIED VALUES:
valueA:
  mapKeyA: mapValueA

COMPUTED VALUES:
valueA:
  mapKeyA: mapValueA
valueB: {}
valueC: 10

HOOKS:
MANIFEST:

---
# Source: example/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: example
---
# Source: example/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: example
data:
  someValue: 10
'''

class TestHelmClient2(unittest.TestCase):
    """
        The kubernetes driver supports multiple versions of helm that have different syntax for the helm commands. This class is to test actions using the Helm 2 syntax.
    """

    def setUp(self):
        self.client = HelmClient('kubeconfig', '2.16.6')

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
        name = self.client.upgrade('chart', 'name', 'namespace')
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
        self.assertEqual(helm_release.released, 'Wed May 13 13:03:30 2020')
        self.assertEqual(helm_release.chart, 'example-chart-0.9.0')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_safe_get_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.safe_get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_safe_get_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.safe_get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 0, EXAMPLE_MANIFEST)
        helm_release = self.client.get('example', 'namespace')
        self.assertIsInstance(helm_release, HelmReleaseDetails)
        self.assertEqual(helm_release.revision, 1)
        self.assertEqual(helm_release.released, 'Wed May 13 13:03:30 2020')
        self.assertEqual(helm_release.chart, 'example-chart-0.9.0')
        self.assertEqual(helm_release.user_supplied_values, {
            'valueA': {
                'mapKeyA': 'mapValueA'
            }
        })
        self.assertEqual(helm_release.computed_values, {
            'valueA': {
                'mapKeyA': 'mapValueA'
            },
            'valueB': {},
            'valueC': 10
        })
        self.assertEqual(helm_release.manifest, [
            {
                'apiVersion': 'v1',
                'kind': 'ServiceAccount',
                'metadata': {
                    'name': 'example'
                }
            },
            {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': 'example'
                },
                'data': {
                    'someValue': 10
                }
            }
        ])

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get_helm_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 1, EXAMPLE_MANIFEST)
        self.assertRaises(HelmError, self.client.get, 'name', 'namespace')

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get_command_error(self, mock_subprocess):
        self.__mock_subprocess_response(mock_subprocess, 127, EXAMPLE_MANIFEST)
        self.assertRaises(HelmCommandNotFoundError, self.client.get, 'name', 'namespace')

