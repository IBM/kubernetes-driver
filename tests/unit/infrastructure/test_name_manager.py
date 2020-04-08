import unittest
import uuid
from kubedriver.infrastructure.name_manager import NameManager

class TestNameManager(unittest.TestCase):

    def setUp(self):
        self.mgr = NameManager()

    def test_safe_label_name_from_resource_id(self):
        resource_id = str(uuid.uuid4())
        result = self.mgr.safe_label_name_from_resource_id(resource_id)
        self.assertEqual(result, resource_id)

    def test_safe_label_name_from_resource_id_removes_special_chars(self):
        resource_id = 'abc@123'
        result = self.mgr.safe_label_name_from_resource_id(resource_id)
        self.assertEqual(result, 'abc123')

    def test_safe_label_name_from_resource_id_removes_uppercase(self):
        resource_id = 'TesTiNg'
        result = self.mgr.safe_label_name_from_resource_id(resource_id)
        self.assertEqual(result, 'testing')

    def test_safe_label_name_from_resource_id_replaces_spaces_and_underscores(self):
        resource_id = 'testing spaces__and_underscores'
        result = self.mgr.safe_label_name_from_resource_id(resource_id)
        self.assertEqual(result, 'testing-spaces-and-underscores')

    def test_safe_label_name_from_resource_id_raises_error_if_exceeds_max_length(self):
        resource_id = 'a' * 64
        with self.assertRaises(ValueError) as context:
            self.mgr.safe_label_name_from_resource_id(resource_id)
        self.assertEqual(str(context.exception), f'Failed to generate safe label name from Resource ID: [\"Attempt \'{resource_id}\' was invalid: Label names must contain no more than 63 characters -> Contained 64\"]')

    def test_safe_label_name_from_resource_name(self):
        resource_name = 'Root__NestedA__LeafA'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'root-nesteda-leafa')

    def test_safe_label_name_from_resource_name_removes_special_chars(self):
        resource_name = 'abc@123'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'abc123')

    def test_safe_label_name_from_resource_name_removes_uppercase(self):
        resource_name = 'TesTiNg'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'testing')

    def test_safe_label_name_from_resource_name_replaces_spaces_and_underscores(self):
        resource_name = 'testing spaces__and_underscores'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'testing-spaces-and-underscores')

    def test_safe_label_name_from_resource_name_shortens_name_if_required(self):
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, over estimate as the double underscores will be reduced to a single dash
        for i in range(30):
            resource_name += f'__Node{i}'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, f'root-node{i}')

    def test_safe_label_name_from_resource_name_removes_vowels_if_required(self):
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, over estimate as the double underscores will be reduced to a single dash
        for i in range(30):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 500 + f'de{i+1}'
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}')

    def test_safe_label_name_from_resource_name_reduces_to_three_characters_if_no_vowels(self):
        resource_name = 'b' * 64
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'bbb')

    def test_safe_label_name_from_resource_name_reduces_to_three_characters_if_all_vowels(self):
        resource_name = 'a' * 64
        result = self.mgr.safe_label_name_from_resource_name(resource_name)
        self.assertEqual(result, 'aaa')

    def test_safe_label_name_for_resource(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root__NodeA__NodeA1__Leaf'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-nodea1-leaf-{resource_id}')

    def test_safe_label_name_for_resource_removes_special_chars(self):
        resource_id = str(uuid.uuid4())
        #LM shouldn't support this anyway but better to be safe
        resource_name = 'Root__Node$A__Node.@A1__Leaf'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-node-a1-leaf-{resource_id}')

    def test_safe_label_name_for_resource_removes_uppercase(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'TesTiNg'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'testing-{str(resource_id)}')

    def test_safe_label_name_for_resource_replaces_spaces_and_underscores(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'space and_under'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'space-and-under-{str(resource_id)}')

    def test_safe_label_name_for_resource_shortens_name_if_required(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        self.assertTrue(len(resource_id)+len(resource_name)>500)
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-node{i}-{resource_id}')

    def test_safe_label_name_for_resource_removes_vowels_if_required(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(30):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 500 + f'de{i+1}'
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}-{resource_id}')

    def test_safe_label_name_for_resource_reduces_name_to_three_characters_if_no_vowels(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(30):
            resource_name += f'__Node{i}'
        #Make the last section all constants
        resource_name += '__'
        resource_name += 'bbb' * 200
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-bbb-{resource_id}')

    def test_safe_label_name_for_resource_reduces_name_to_three_characters_if_all_vowels(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(30):
            resource_name += f'__Node{i}'
        #Make the last section all vowels
        resource_name += '__'
        resource_name += 'aaa' * 200
        result = self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-aaa-{resource_id}')

    def test_safe_label_name_for_resource_raises_error_if_exceeds_max_length(self):
        #Make the ID long so even after reducing the name, the full string exceeds max length
        resource_id = str(uuid.uuid4()) * 20
        resource_name = 'Root'
        with self.assertRaises(ValueError) as context:
            self.mgr.safe_label_name_for_resource(resource_id, resource_name)
        self.assertEqual(str(context.exception), f'Failed to generate safe label name for Resource: [\"Attempt \'root-{resource_id}\' was invalid: Label names must contain no more than 63 characters -> Contained 725\", '+\
            f'\"Attempt \'rt-{resource_id}\' was invalid: Label names must contain no more than 63 characters -> Contained 723\"]')

    def test_safe_subdomain_name_from_resource_id(self):
        resource_id = str(uuid.uuid4())
        result = self.mgr.safe_subdomain_name_from_resource_id(resource_id)
        self.assertEqual(result, resource_id)

    def test_safe_subdomain_name_from_resource_id_removes_special_chars(self):
        resource_id = 'abc@123'
        result = self.mgr.safe_subdomain_name_from_resource_id(resource_id)
        self.assertEqual(result, 'abc123')

    def test_safe_subdomain_name_from_resource_id_removes_uppercase(self):
        resource_id = 'TesTiNg'
        result = self.mgr.safe_subdomain_name_from_resource_id(resource_id)
        self.assertEqual(result, 'testing')

    def test_safe_subdomain_name_from_resource_id_replaces_spaces_and_underscores(self):
        resource_id = 'testing spaces__and_underscores'
        result = self.mgr.safe_subdomain_name_from_resource_id(resource_id)
        self.assertEqual(result, 'testing-spaces-and-underscores')

    def test_safe_subdomain_name_from_resource_id_raises_error_if_exceeds_max_length(self):
        resource_id = 'a' * 254
        with self.assertRaises(ValueError) as context:
            self.mgr.safe_subdomain_name_from_resource_id(resource_id)
        self.assertEqual(str(context.exception), f'Failed to generate safe subdomain name from Resource ID: [\"Attempt \'{resource_id}\' was invalid: Subdomain names must contain no more than 253 characters -> Contained 254\"]')

    def test_safe_subdomain_name_from_resource_name(self):
        resource_name = 'Root__NestedA__LeafA'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'root-nesteda-leafa')

    def test_safe_subdomain_name_from_resource_name_removes_special_chars(self):
        resource_name = 'abc@123'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'abc123')

    def test_safe_subdomain_name_from_resource_name_removes_uppercase(self):
        resource_name = 'TesTiNg'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'testing')

    def test_safe_subdomain_name_from_resource_name_replaces_spaces_and_underscores(self):
        resource_name = 'testing spaces__and_underscores'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'testing-spaces-and-underscores')

    def test_safe_subdomain_name_from_resource_name_shortens_name_if_required(self):
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, over estimate as the double underscores will be reduced to a single dash
        for i in range(50):
            resource_name += f'__Node{i}'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, f'root-node{i}')

    def test_safe_subdomain_name_from_resource_name_removes_vowels_if_required(self):
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, over estimate as the double underscores will be reduced to a single dash
        for i in range(30):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 300 + f'de{i+1}'
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}')

    def test_safe_subdomain_name_from_resource_name_reduces_to_three_characters_if_no_vowels(self):
        resource_name = 'b' * 254
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'bbb')

    def test_safe_subdomain_name_from_resource_name_reduces_to_three_characters_if_all_vowels(self):
        resource_name = 'a' * 254
        result = self.mgr.safe_subdomain_name_from_resource_name(resource_name)
        self.assertEqual(result, 'aaa')

    def test_safe_subdomain_name_for_resource(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root__NodeA__NodeA1__Leaf'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-nodea1-leaf-{resource_id}')

    def test_safe_subdomain_name_for_resource_removes_special_chars(self):
        resource_id = str(uuid.uuid4())
        #LM shouldn't support this anyway but better to be safe
        resource_name = 'Root__Node$A__Node.@A1__Leaf'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-nodea-node.a1-leaf-{resource_id}')

    def test_safe_subdomain_name_for_resource_removes_uppercase(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'TesTiNg'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'testing-{str(resource_id)}')

    def test_safe_subdomain_name_for_resource_replaces_spaces_and_underscores(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'space and_under'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'space-and-under-{str(resource_id)}')

    def test_safe_subdomain_name_for_resource_shortens_name_if_required(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(300):
            resource_name += f'__Node{i}'
        self.assertTrue(len(resource_id)+len(resource_name)>500)
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'root-node{i}-{resource_id}')

    def test_safe_subdomain_name_for_resource_removes_vowels_if_required(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(50):
            resource_name += f'__Node{i}'
        #Make the last section ridiclously long with vowels
        resource_name += '__VowelNo' + ('o') * 500 + f'de{i+1}'
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-vwlnd{i+1}-{resource_id}')

    def test_safe_subdomain_name_for_resource_reduces_name_to_three_characters_if_no_vowels(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(50):
            resource_name += f'__Node{i}'
        #Make the last section all constants
        resource_name += '__'
        resource_name += 'bbb' * 200
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-bbb-{resource_id}')

    def test_safe_subdomain_name_for_resource_reduces_name_to_three_characters_if_all_vowels(self):
        resource_id = str(uuid.uuid4())
        resource_name = 'Root'
        #Make sure we have a name far exceeding the max length, as some parts of it will be removed
        for i in range(50):
            resource_name += f'__Node{i}'
        #Make the last section all vowels
        resource_name += '__'
        resource_name += 'aaa' * 200
        result = self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(result, f'rt-aaa-{resource_id}')

    def test_safe_subdomain_name_for_resource_raises_error_if_exceeds_max_length(self):
        #Make the ID long so even after reducing the name, the full string exceeds max length
        resource_id = str(uuid.uuid4()) * 20
        resource_name = 'Root'
        with self.assertRaises(ValueError) as context:
            self.mgr.safe_subdomain_name_for_resource(resource_id, resource_name)
        self.assertEqual(str(context.exception), f'Failed to generate safe subdomain name for Resource: [\"Attempt \'root-{resource_id}\' was invalid: Subdomain names must contain no more than 253 characters -> Contained 725\", '+\
            f'\"Attempt \'rt-{resource_id}\' was invalid: Subdomain names must contain no more than 253 characters -> Contained 723\"]')
