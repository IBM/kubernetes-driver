import unittest
import kubedriver.location as location

class TestImports(unittest.TestCase):

    def test_deployment_location(self):
        imported = location.KubeDeploymentLocation
