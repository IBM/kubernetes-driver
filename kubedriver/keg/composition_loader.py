from kubedriver.kubeobjects import ObjectConfiguration

class CompositionLoader:

    def __init__(self, api_ctl, helm_client):
        self.api_ctl = api_ctl
        self.helm_client = helm_client

    def load_composition(self, keg_status, include_helm_objects=True):
        composition = {}
        composition['objects'] = self.load_composition_objects(keg_status)
        composition['helm_releases'] = self.load_composition_helm_releases(keg_status, include_objects=include_helm_objects)
        return composition

    def load_composition_objects(self, keg_status):
        result = []
        if keg_status.composition != None:
            if keg_status.composition.objects != None:
                for object_status in keg_status.composition.objects:
                    found, obj = self.api_ctl.safe_read_object(object_status.group, object_status.kind, object_status.name, namespace=object_status.namespace)
                    if found:
                        as_dict = self.api_ctl.base_kube_client.sanitize_for_serialization(obj)
                        result.append(as_dict)
        return result

    def load_composition_helm_releases(self, keg_status, include_objects=True):
        result = []
        if keg_status.composition != None:
            if keg_status.composition.helm_releases != None:
                for helm_release in keg_status.composition.helm_releases:
                    found, helm_release_details = self.helm_client.safe_get(helm_release.name, helm_release.namespace)
                    if found:
                        helm_release_details_as_dict = self.api_ctl.base_kube_client.sanitize_for_serialization(helm_release_details)
                        if include_objects:
                            objects = self.load_objects_in_helm_release(helm_release_details)
                            helm_release_details_as_dict['objects'] = objects
                        result.append(helm_release_details_as_dict)
        return result

    def load_objects_in_helm_release(self, helm_release_details):
        result = []
        if helm_release_details.manifest != None:
            for manifest_entry in helm_release_details.manifest:
                object_config = ObjectConfiguration(manifest_entry)
                if self.api_ctl.is_object_namespaced(object_config.api_version, object_config.kind):
                    if object_config.namespace != None:
                        namespace = object_config.namespace
                    else:
                        namespace = helm_release_details.namespace
                else:
                    namespace = None
                found, obj = self.api_ctl.safe_read_object(object_config.api_version, object_config.kind, object_config.name, namespace=namespace)
                if found:
                    as_dict = self.api_ctl.base_kube_client.sanitize_for_serialization(obj)
                    result.append(as_dict)
        return result