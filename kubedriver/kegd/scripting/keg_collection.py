

class KegCollection:

    def __init__(self, composition):
        self.__composition = composition
        self.objects = ObjectsCollection(composition.get('objects', []))
        self.helm_releases = HelmReleasesCollection(composition.get('helm_releases', []))

class ObjectsCollection:

    def __init__(self, objects, default_namespace=None):
        self.__objects = objects
        self.__default_namespace = default_namespace

    def _a_new_me(self, with_objects):
        return ObjectsCollection(with_objects)

    def get(self, group, kind, name, namespace=None):
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

    def get_by_labels(self, **kwargs):
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

    def getByLabels(self, **labels):
        return self.get_by_labels(**labels)

    def filter_by_kind(self, group, kind):
        subset = []
        for obj in self.__objects:
            if (obj.get('apiVersion') == group and obj.get('kind') == kind):
                subset.append(obj)
        return self._a_new_me(subset)

    def filterByKind(self, group, kind):
        return self.filter_by_kind(group, kind)

class HelmReleasesCollection:

    def __init__(self, helm_releases):
        self.__helm_releases = []
        for entry in helm_releases:
            self.__helm_releases.append(HelmReleaseCollection(entry))

    def get(self, name, namespace):
        for helm_release in self.__helm_releases:
            if helm_release.info.get('name') == name and helm_release.info.get('namespace') == namespace:
                return True, helm_release
        return False, None

class HelmReleaseCollection:

    def __init__(self, helm_release):
        self.__helm_release = helm_release
        if 'objects' in self.__helm_release:
            objects = self.__helm_release.pop('objects')
        else:
            objects = []
        self.__objects = ObjectsCollection(objects)

    @property
    def info(self):
        return self.__helm_release

    @property
    def objects(self):
        return self.__objects
