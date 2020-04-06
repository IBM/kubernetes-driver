import unittest
import uuid
from kubedriver.infrastructure.name_manager import NameManager

class TestNameManager(unittest.TestCase):

    def test_safe_subdomain_name_for_resource(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root__NodeA__NodeA1__Leaf'
        result = mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-nodea1-leaf-{resource_id}')

    def test_safe_subdomain_name_for_resource_removes_special_chars(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        #LM shouldn't support this anyway but better to be safe
        resource_name = 'Root__Node$A__Node.@A1__Leaf'
        result = mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-node.a1-leaf-{resource_id}')

    def test_safe_subdomain_name_for_resource_shortens_name(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        self.assertTrue(len(resource_id)+len(resource_name)>500)
        result = mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-node{i}-{resource_id}')

    def test_safe_subdomain_name_for_resource_shortens_name_and_removes_vowels(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 500 + f'de{i+1}'
        result = mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}-{resource_id}')

    def test_safe_label_name_for_resource(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root__NodeA__NodeA1__Leaf'
        result = mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-nodea1-leaf-{resource_id}')

    def test_safe_label_name_for_resource_removes_special_chars(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        #LM shouldn't support this anyway but better to be safe
        resource_name = 'Root__Node$A__Node.@A1__Leaf'
        result = mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-node-a1-leaf-{resource_id}')

    def test_safe_label_name_for_resource_shortens_name(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        self.assertTrue(len(resource_id)+len(resource_name)>500)
        result = mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-node{i}-{resource_id}')

    def test_safe_label_name_for_resource_shortens_name_and_removes_vowels(self):
        mgr = NameManager()
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 500 + f'de{i+1}'
        result = mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}-{resource_id}')
