import unittest
import kubedriver.templating as templating

class TestImports(unittest.TestCase):

    def test_template(self):
        imported = templating.Template 
