from kubedriver.kegd.model import V1alpha1KegdCompositionDelta, V1alpha1HelmReleaseDelta, V1alpha1ObjectDelta, V1alpha1KegdCompositionDeltaSubset

class KegDeltaCapture:

    def __init__(self, existing_delta=None):
        self.delta = existing_delta if existing_delta is not None else V1alpha1KegdCompositionDelta()

    def __add(self, item, to_list):
        if item not in to_list:
            to_list.append(item)
            return True
        return False

    def __remove(self, item, from_list):
        if item in from_list:
            from_list.remove(item)
            return True
        return False

    def __add_helm(self, item, to_list):
        if not self.__add(item, to_list):
            existing = to_list[to_list.index(item)]
            if item.deployed_objects != None:
                if existing.deployed_objects == None:
                    existing.deployed_objects = item.deployed_objects
                else:
                    existing.deployed_objects.extend(item.deployed_objects)
            if item.removed_objects != None:
                if existing.removed_objects == None:
                    existing.removed_objects = item.removed_objects
                else:
                    existing.removed_objects.extend(item.removed_objects)

    def __remove_helm(self, item, from_list):
        return self.__remove(item, from_list)

    def deployed_object(self, obj_status):
        self.__init_deployed_objects()
        new_entry = V1alpha1ObjectDelta(group=obj_status.group, kind=obj_status.kind, name=obj_status.name, namespace=obj_status.namespace, uid=obj_status.uid)
        self.__add(new_entry, self.delta.deployed.objects)
        if self.delta.removed != None and self.delta.removed.objects != None:
            self.__remove(new_entry, self.delta.removed.objects)

    def removed_object(self, obj_status):
        self.__init_removed_objects()
        new_entry = V1alpha1ObjectDelta(group=obj_status.group, kind=obj_status.kind, name=obj_status.name, namespace=obj_status.namespace, uid=obj_status.uid)
        self.__add(new_entry, self.delta.removed.objects)
        if self.delta.deployed != None and self.delta.deployed.objects != None:
            self.__remove(new_entry, self.delta.deployed.objects)

    def deployed_helm_release(self, helm_release_status, objects_only=False, deployed_objects=None, removed_objects=None):
        self.__init_deployed_helm_releases()
        parsed_objs = None
        if deployed_objects != None and len(deployed_objects) > 0:
            parsed_objs = [V1alpha1ObjectDelta(group=obj.group, kind=obj.kind, name=obj.name, namespace=obj.namespace, uid=obj.uid) for obj in deployed_objects]
        #Upgrades may remove objects
        parsed_removed_objs = None
        if removed_objects != None and len(removed_objects) > 0:
            parsed_removed_objs = [V1alpha1ObjectDelta(group=obj.group, kind=obj.kind, name=obj.name, namespace=obj.namespace, uid=obj.uid) for obj in removed_objects]
        new_entry = V1alpha1HelmReleaseDelta(name=helm_release_status.name, namespace=helm_release_status.namespace, objects_only=objects_only, deployed_objects=parsed_objs, removed_objects=parsed_removed_objs)
        self.__add_helm(new_entry, self.delta.deployed.helm_releases)
        if self.delta.removed != None and self.delta.removed.helm_releases != None:
            self.__remove(new_entry, self.delta.removed.helm_releases)

    def removed_helm_release(self, helm_release_status, removed_objects=None):
        self.__init_removed_helm_releases()
        parsed_objs = None
        if removed_objects != None and len(removed_objects) > 0:
            parsed_objs = [V1alpha1ObjectDelta(group=obj.group, kind=obj.kind, name=obj.name, namespace=obj.namespace, uid=obj.uid) for obj in removed_objects]
        new_entry = V1alpha1HelmReleaseDelta(name=helm_release_status.name, namespace=helm_release_status.namespace, removed_objects=parsed_objs)
        self.__add_helm(new_entry, self.delta.removed.helm_releases)
        if self.delta.deployed != None and self.delta.deployed.helm_releases != None:
            self.__remove(new_entry, self.delta.deployed.helm_releases)

    def __init_deployed(self):
        if self.delta.deployed == None:
            self.delta.deployed = V1alpha1KegdCompositionDeltaSubset()

    def __init_deployed_objects(self):
        self.__init_deployed()
        if self.delta.deployed.objects == None:
            self.delta.deployed.objects = []

    def __init_deployed_helm_releases(self):
        self.__init_deployed()
        if self.delta.deployed.helm_releases == None:
            self.delta.deployed.helm_releases = []

    def __init_removed(self):
        if self.delta.removed == None:
            self.delta.removed = V1alpha1KegdCompositionDeltaSubset()

    def __init_removed_objects(self):
        self.__init_removed()
        if self.delta.removed.objects == None:
            self.delta.removed.objects = []

    def __init_removed_helm_releases(self):
        self.__init_removed()
        if self.delta.removed.helm_releases == None:
            self.delta.removed.helm_releases = []

    def __get_existing_helm_release(self, helm_release_status, from_list):
        for item in from_list:
            if item.name == helm_release_status.name and item.namespace == helm_release_status.namespace:
                return item
        return None
