import unittest
import kubedriver.keg as keg

class TestImports(unittest.TestCase):

    def test_entity_group(self):
        imported = keg.EntityGroup

    def test_entity_group_manager(self):
        imported = keg.EntityGroupManager

    def test_config_map_record_persistence(self):
        imported = keg.ConfigMapRecordPersistence

    def test_manager_context(self):
        imported = keg.ManagerContext

    def test_manager_context_loader(self):
        imported = keg.ManagerContextLoader
