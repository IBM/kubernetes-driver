import unittest
import yaml
from unittest.mock import MagicMock
from kubedriver.infrastructure.converter import InfrastructureConverter
from kubedriver.infrastructure.template_types import TemplateTypes
from kubedriver.infrastructure.render_context import ExtendedResourceTemplateContext
from ignition.utils.propvaluemap import PropValueMap
from ignition.service.templating import Jinja2TemplatingService

class TestInfrastructureConverter(unittest.TestCase):

    def setUp(self):
        self.converter = InfrastructureConverter(templating=Jinja2TemplatingService(), template_context_builder=ExtendedResourceTemplateContext())
        self.kube_location = MagicMock(default_object_namespace='default')

    def __mock_properties(self):
        properties = {}
        properties['propA'] = {'type': 'string', 'value': 'A'}
        properties['propB'] = {'type': 'string', 'value': 'B'}
        properties['propC'] = {'type': 'string', 'value': 'C'}
        properties_map = PropValueMap(properties)
        system_properties = {}
        system_properties['resourceId'] = {'type': 'string', 'value': '123'}
        system_properties['resourceName'] = {'type': 'string', 'value': 'Resource-A'}
        system_properties_map = PropValueMap(system_properties)
        return system_properties_map, properties_map