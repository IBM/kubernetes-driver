from kubedriver.utils.to_dict import to_dict

class CompositionReader:

    def load_composition(self, keg_status, api_ctl):
        objects = []
        if keg_status.composition != None:
            if keg_status.composition.objects != None:
                for object_status in keg_status.composition.objects:
                    found, obj = api_ctl.safe_read_object(object_status.group, object_status.kind, object_status.name, namespace=object_status.namespace)
                    if found:
                        if api_ctl.is_object_custom(object_status.group, object_status.kind):
                            objects.append(obj)
                        else:
                            objects.append(to_dict(obj)) 
        return objects