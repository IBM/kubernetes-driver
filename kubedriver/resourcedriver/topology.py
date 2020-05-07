import json
from ignition.model.associated_topology import AssociatedTopologyEntry, AssociatedTopology

class KubernetesAssociatedTopology(AssociatedTopology):
    KEG_ENTRY_NAME = 'keg'
    
    def add_keg_entry(self, keg_name, kube_location):
        keg_type = self._build_type_string(kube_location.cm_api_version, kube_location.cm_kind)
        self.add_entry(KubernetesAssociatedTopology.KEG_ENTRY_NAME, keg_name, keg_type)

    def _build_type_string(self, api_version, kind):
        return json.dumps({
            'api_version': api_version, 
            'kind': kind
        })
