import unittest
import kubedriver.locationcontext as locationcontext

class TestImports(unittest.TestCase):

    def test_factory(self):
        imported = locationcontext.LocationContextFactory

    def test_context(self):
        imported = locationcontext.LocationContext
