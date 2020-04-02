import unittest
import kubedriver.kubegroup as kubegroup

class TestImports(unittest.TestCase):

    def test_entity_group(self):
        imported = kubegroup.EntityGroup

    def test_entity_group_manager(self):
        imported = kubegroup.EntityGroupManager

    def test_config_map_record_persistence(self):
        imported = kubegroup.ConfigMapRecordPersistence

    def test_manager_context(self):
        imported = kubegroup.ManagerContext

    def test_manager_context_loader(self):
        imported = kubegroup.ManagerContextLoader
