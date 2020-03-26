import unittest
import kubedriver.manager as manager

class TestImports(unittest.TestCase):

    def test_kube_object_manager(self):
        imported = manager.KubeObjectManager

    def test_config_map_record_persistence(self):
        imported = manager.ConfigMapRecordPersistence

    def test_manager_context(self):
        imported = manager.ManagerContext

    def test_manager_context_loader(self):
        imported = manager.ManagerContextLoader
