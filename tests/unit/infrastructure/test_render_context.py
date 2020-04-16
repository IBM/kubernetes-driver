import unittest
from unittest.mock import patch
from kubedriver.infrastructure.render_context import ExtendedResourceTemplateContext
from ignition.utils.propvaluemap import PropValueMap

class TestExtendedResourceTemplateContext(unittest.TestCase):

    @patch('kubedriver.infrastructure.render_context.NameManager')
    def test_build(self, name_manager):
        service = ExtendedResourceTemplateContext()
        name_manager.return_value.safe_label_name_for_resource.return_value = 'resource-label'
        name_manager.return_value.safe_subdomain_name_for_resource.return_value = 'resource-subdomain'
        name_manager.return_value.safe_label_name_from_resource_id.return_value = 'resource-id-label'
        name_manager.return_value.safe_subdomain_name_from_resource_id.return_value = 'resource-id-subdomain'
        name_manager.return_value.safe_label_name_from_resource_name.return_value = 'resource-name-label'
        name_manager.return_value.safe_subdomain_name_from_resource_name.return_value = 'resource-name-subdomain'
        properties = PropValueMap({'propA': {'type': 'string', 'value': 'A'}, 'propB': {'type': 'string', 'value': 'B'}})
        system_properties = PropValueMap({'resourceId': {'type': 'string', 'value': '123-456-789'}, 'resourceName': {'type': 'string', 'value': 'Testing'}})
        deployment_location = {
            'name': 'Test',
            'type': 'Kubernetes',
            'properties': {
                'dlPropA': 'A DL Prop'
            }
        }
        result = service.build(system_properties, properties, deployment_location)
        self.maxDiff = None
        self.assertEqual(result, {
            'propA': 'A',
            'propB': 'B',
            'systemProperties': {
                'resourceLabel': 'resource-label',
                'resourceSd': 'resource-subdomain',
                'resourceSubdomain': 'resource-subdomain',
                'resourceId': '123-456-789',
                'resourceIdSd': 'resource-id-subdomain',
                'resourceIdSubdomain': 'resource-id-subdomain',
                'resourceIdLabel': 'resource-id-label',
                'resourceName': 'Testing',
                'resourceNameSd': 'resource-name-subdomain',
                'resourceNameSubdomain': 'resource-name-subdomain',
                'resourceNameLabel': 'resource-name-label'
            },
            'deploymentLocationInst': {
                'name': 'Test',
                'type': 'Kubernetes',
                'properties': {
                    'dlPropA': 'A DL Prop'
                }
            }
        })


