import unittest
import yaml
from unittest.mock import MagicMock
from kubedriver.infrastructure.converter import InfrastructureConverter
from kubedriver.infrastructure.template_types import TemplateTypes
from kubedriver.infrastructure.render_context import ExtendedResourceTemplateContext
from ignition.utils.propvaluemap import PropValueMap
from ignition.service.templating import Jinja2TemplatingService

multi_obj_template = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ systemProperties.resourceSd }}
data:
  dataValue: {{ propA }}
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: {{ systemProperties.resourceSd }}
spec:
  rules:
  - host: {{ propB }}
    http:
      paths:
      - path: /
        backend:
         serviceName: test
         servicePort: 7777
'''

multi_obj_config_1 = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: resource-a-123
data:
  dataValue: A
'''
multi_obj_config_2 = '''
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: resource-a-123
spec:
  rules:
  - host: B
    http:
      paths:
      - path: /
        backend:
         serviceName: test
         servicePort: 7777
'''

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

    def test_convert_to_entity_group_with_objects(self):
        system_properties, properties = self.__mock_properties()
        entity_group = self.converter.convert_to_entity_group(multi_obj_template, TemplateTypes.OBJECT_CONFIG, system_properties, properties, self.kube_location)
        self.assertEqual(entity_group.uid, 'resource-a-123')
        self.assertEqual(len(entity_group.helm_releases), 0)
        self.assertEqual(len(entity_group.objects), 2)
        self.assertEqual(entity_group.objects[0].data, yaml.safe_load(multi_obj_config_1))
        self.assertEqual(entity_group.objects[1].data, yaml.safe_load(multi_obj_config_2))

        