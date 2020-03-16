import unittest
import kubedriver.manager as manager

class TestImports(unittest.TestCase):

    def test_kube_object_manager(self):
        imported = manager.KubeObjectManager

    def test_deployed_object_group_record(self):
        imported = manager.DeployedObjectGroupRecord

    def test_deployed_object_record(self):
        imported = manager.DeployedObjectRecord

    def test_config_map_record_persistence(self):
        imported = manager.ConfigMapRecordPersistence
