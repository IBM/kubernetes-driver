import unittest
import kubedriver.kubeobjects as kubeobjects

class TestImports(unittest.TestCase):

    def test_object_configuration_document(self):
        imported = kubeobjects.ObjectConfigurationDocument

    def test_object_configuration_template(self):
        imported = kubeobjects.ObjectConfigurationTemplate

    def test_object_configuration(self):
        imported = kubeobjects.ObjectConfiguration

    def test_object_configuration_group(self):
        imported = kubeobjects.ObjectConfigurationGroup

    def test_invalid_object_configuration_error(self):
        imported = kubeobjects.InvalidObjectConfigurationError

    def test_templating(self):
        imported = kubeobjects.Templating

    def test_namehelper(self):
        imported = kubeobjects.NameHelper
        imported = kubeobjects.namehelper
