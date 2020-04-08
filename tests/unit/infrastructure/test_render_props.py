import unittest
from unittest.mock import patch
from kubedriver.infrastructure.render_props import RenderPropsBuilder
from ignition.utils.propvaluemap import PropValueMap

class TestRenderPropsBuilder(unittest.TestCase):

    @patch('kubedriver.infrastructure.render_props.NameManager')
    def test_build(self, name_manager):
        name_manager.return_value.safe_label_name_for_resource.return_value = 'resource-label'
        name_manager.return_value.safe_subdomain_name_for_resource.return_value = 'resource-subdomain'
        name_manager.return_value.safe_label_name_from_resource_id.return_value = 'resource-id-label'
        name_manager.return_value.safe_subdomain_name_from_resource_id.return_value = 'resource-id-subdomain'
        name_manager.return_value.safe_label_name_from_resource_name.return_value = 'resource-name-label'
        name_manager.return_value.safe_subdomain_name_from_resource_name.return_value = 'resource-name-subdomain'
        properties = PropValueMap({'propA': {'type': 'string', 'value': 'A'}, 'propB': {'type': 'string', 'value': 'B'}})
        system_properties = PropValueMap({'resourceId': {'type': 'string', 'value': '123-456-789'}, 'resourceName': {'type': 'string', 'value': 'Testing'}})
        result = RenderPropsBuilder.build(system_properties, properties)
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
            }
        })