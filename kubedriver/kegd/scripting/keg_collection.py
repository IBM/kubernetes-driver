

class KegCollection:

    def __init__(self, objects):
        self.__objects = objects

    def get_object(self, group, kind, name, namespace=None):
        for obj in self.__objects:
            if (obj.get('api_version') == group 
                and obj.get('kind') == kind):
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