import unittest
import kubedriver.location as location

class TestImports(unittest.TestCase):

    def test_deployment_location(self):
        imported = location.KubeDeploymentLocation

    def test_invalid_deployment_location_error(self):
        imported = location.InvalidDeploymentLocationError

    def test_deployment_location_translator(self):
        imported = location.KubeDeploymentLocationTranslator
