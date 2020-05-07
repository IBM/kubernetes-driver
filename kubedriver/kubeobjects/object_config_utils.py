from .object_config import ObjectConfiguration
from .object_attrs import ObjectAttributes

class ObjectConfigUtils:
    
    def add_label(self, config, key, value):
        if type(config) == ObjectConfiguration:
            data = config.data
        else:
            data = config
        if data.get(ObjectAttributes.METADATA) == None:
            data[ObjectAttributes.METADATA] = {}
        metadata = data.get(ObjectAttributes.METADATA)
        if metadata.get(ObjectAttributes.LABELS) == None:
            metadata[ObjectAttributes.LABELS] = {}
        labels = metadata.get(ObjectAttributes.LABELS)
        labels[key] = value
        