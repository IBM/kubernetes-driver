import unittest
import yaml
from unittest.mock import MagicMock
from kubedriver.infrastructure import InfrastructureDriver
from kubedriver.location import KubeDeploymentLocation
from kubedriver.kubeobjects import ObjectConfigurationDocument
from kubedriver.kubegroup import EntityGroup
from ignition.utils.propvaluemap import PropValueMap

single_obj_template = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ resourceNameSd }}
data:
  dataValue: {{ propA }}
'''

single_obj_doc = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: resource-a
data:
  dataValue: A
'''

class ObjectConfigurationMatcher:

    def __init__(self, expected_conf):
        self.expected_conf = expected_conf

    def __eq__(self, other):
        return other.conf == self.expected_conf

    def __str__(self):
        return str(self.expected_conf)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.expected_conf!r})'


class TestInfrastructureDriver():#unittest.TestCase):

    def setUp(self):
        self.deployment_location_translator = MagicMock()
        self.location_based_management = MagicMock()
        self.group_manager = MagicMock()
        self.location_based_management.build_manager.return_value = self.group_manager
        self.templating = MagicMock()
        self.driver = InfrastructureDriver(self.deployment_location_translator, self.location_based_management, self.templating)

    def __mock_single_object_template(self):
        template = single_obj_template
        doc_content = single_obj_doc
        self.templating.render_template.return_value = ObjectConfigurationDocument(doc_content)
        return template, 'Kubernetes', doc_content

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

    def __mock_location(self):
        deployment_location = {
            'name': 'Test',
            'properties': {
                'clientConfig': 'client_config'
            }
        }
        self.deployment_location_translator.translate.return_value = KubeDeploymentLocation('Test', 'client_config')
        return deployment_location

    def test_create_infrastructure_single_object(self):
        template, template_type, expected_doc_content = self.__mock_single_object_template()
        system_properties, properties = self.__mock_properties()
        deployment_location = self.__mock_location()
        result = self.driver.create_infrastructure(template, template_type, system_properties, properties, deployment_location)
        self.assertEqual(result.infrastructure_id, '{0}.{1}'.format(system_properties['resourceName'], system_properties['resourceId']))
        self.assertIsNotNone(result.request_id)
        self.group_manager.create_group.assert_called_once()
        args, kwargs = self.group_manager.create_group.call_args
        self.assertEqual(len(args), 1)
        self.assertIsInstance(args[0], EntityGroup)
        group = args[0]
        self.assertEqual(group.uid, '{0}.{1}'.format(system_properties['resourceName'], system_properties['resourceId']))
        self.assertEqual(len(group.objects), 1)
        obj = group.objects[0]
        self.assertEqual(obj.conf, yaml.safe_load(expected_doc_content))

    def test_create_infrastructure_templates_with_properties(self):
        template, template_type, expected_doc_content = self.__mock_single_object_template()
        system_properties, properties = self.__mock_properties()
        deployment_location = self.__mock_location()
        result = self.driver.create_infrastructure(template, template_type, system_properties, properties, deployment_location)
        self.assertEqual(result.infrastructure_id, '{0}.{1}'.format(system_properties['resourceName'], system_properties['resourceId']))
        self.assertIsNotNone(result.request_id)
        self.templating.render_template.assert_called_once_with(template, {
            'propA': 'A',
            'propB': 'B', 
            'propC': 'C',
            'systemProperties': {
                'resourceId': '123',
                'resourceName': 'Resource-A',
                'resourceIdSd': '123',
                'resourceNameSd': 'resource-a',
                'resourceIdSubdomain': '123',
                'resourceNameSubdomain': 'resource-a'
            }
        })