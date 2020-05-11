import unittest
import kubedriver.keg.records as records

class TestImports(unittest.TestCase):

    def test_group_record(self):
        imported = records.EntityGroupRecord

    def test_object_record(self):
        imported = records.ObjectRecord

    def test_entity_states(self):
        imported = records.EntityStates

    def test_request_record(self):
        imported = records.RequestRecord

    def test_request_states(self):
        imported = records.RequestStates

    def test_request_operations(self):
        imported = records.RequestOperations

