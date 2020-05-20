import unittest
import uuid
from kubedriver.resourcedriver.name_manager import NameManager

class TestNameManager(unittest.TestCase):

    def setUp(self):
        self.mgr = NameManager()

    def test_safe_label_name_from_resource(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'asm_assembly_to_be_referenced__resource'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name, prefix='keg')
        
