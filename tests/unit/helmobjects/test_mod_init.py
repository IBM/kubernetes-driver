import unittest
import kubedriver.helmobjects as helmobjects

class TestImports(unittest.TestCase):

    def test_helm_release_details(self):
        imported = helmobjects.HelmReleaseDetails
