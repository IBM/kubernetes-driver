import unittest
import kubedriver.infrastructure as infrastructure

class TestImports(unittest.TestCase):

    def test_driver(self):
        imported = infrastructure.InfrastructureDriver

    def test_infrastructure_converter(self):
        imported = infrastructure.InfrastructureConverter

    def test_render_context(self):
        imported = infrastructure.ExtendedResourceTemplateContext