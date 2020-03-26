import unittest
import kubedriver.infrastructure as infrastructure

class TestImports(unittest.TestCase):

    def test_driver(self):
        imported = infrastructure.InfrastructureDriver