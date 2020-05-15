import unittest
from unittest.mock import patch, MagicMock
from kubedriver.helmclient import HelmClient
from kubedriver.helmobjects import HelmReleaseDetails

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

class TestHelmClient(unittest.TestCase):

    def setUp(self):
        self.client = HelmClient('kubeconfig', '2.16.6')

    def tearDown(self):
        self.client.close()

    def __mock_subprocess_reponse(self, mock_subprocess, returncode, stdout):
        mock_subprocess.run.return_value = MagicMock(returncode=returncode, stdout=stdout)

    @patch('kubedriver.helmclient.client.subprocess')
    def test_get(self, mock_subprocess):
        self.__mock_subprocess_reponse(mock_subprocess, 0, EXAMPLE_MANIFEST)
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

