

class KegCollection:

    def __init__(self, composition):
        self.__composition = composition
        self.__object_collection = ObjectsCollection(composition.get('objects', {}))
        self.__helm_releases_collection = HelmReleasesCollection(composition.get('helm_releases', {}))

    def get_object(self, group, kind, name, namespace=None):
        return self.__object_collection.get_object(group, kind, name, namespace=namespace)

    def getObject(self, group, kind, name, namespace=None):
        return self.get_object(group, kind, name, namespace=namespace)

    def get_helm_release(self, name, namespace):
        return self.__helm_releases_collection.get_helm_release(name, namespace)

    def getHelmRelease(self, name, namespace):
        return self.get_helm_release(name, namespace)

class ObjectsCollection:

    def __init__(self, objects):
        self.__objects = objects

    def __a_new_me(self, with_objects):
        return ObjectsCollection(with_objects)

    def get_object(self, group, kind, name, namespace=None):
        for obj in self.__objects:
            if (obj.get('apiVersion') == group and obj.get('kind') == kind):
                if obj.get('metadata') != None:
                    metadata = obj.get('metadata')
                    if metadata.get('name') == name:
                        if metadata.get('namespace') != None:
                            if metadata.get('namespace') == namespace:
                                return True, obj
                        elif namespace == None:
                            return True, obj
        return False, None

    def getObject(self, group, kind, name, namespace=None):
        return self.get_object(group, kind, name, namespace=namespace)

    def get_objects_by_labels(self, **kwargs):
        result = []
        for obj in self.__objects:
            metadata = obj.get('metadata')
            if metadata != None:
                labels = metadata.get('labels')
                if labels != None:
                    for k, v in kwargs.items():
                        if k in labels and labels[k] == v:
                            result.append(obj)
        return result

    def getObjectsByLabels(self, **kwargs):
        return self.get_objects_by_labels(**kwargs)

    def ofKind(self, group, kind):
        subset = []
        for obj in self.__objects:
            

                
class HelmReleasesCollection:

    def __init__(self, helm_releases):
        self.__helm_releases = helm_releases
        for entry in self.__helm_releases:
            if 'objects' in entry:
                objects = entry['objects']
            else:
                objects = []
            entry['objects'] = ObjectsCollection(objects)

    def get_helm_release(self, name, namespace):
        for helm_release in self.__helm_releases:
            if helm_release.get('name') == name and helm_release.get('namespace') == namespace:
                print(f'Found {helm_release.get("objects")}')
                return True, helm_release
        return False, None
