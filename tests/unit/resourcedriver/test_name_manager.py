import unittest
import uuid
from kubedriver.resourcedriver.name_manager import NameManager

class TestNameManager(unittest.TestCase):

    def setUp(self):
        self.mgr = NameManager()

    def test_safe_label_name_from_resource_uses_id_as_fallback(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'asm_assembly_to_be_referenced__resource'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name, prefix='keg')
        self.assertEqual(result, f'keg-{resource_id}')
        
    def test_safe_label_name_from_resource_uses_id_as_fallback_no_prefix(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'deploy-firewall-env8-deploy-firewall-rs'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, resource_id)
        