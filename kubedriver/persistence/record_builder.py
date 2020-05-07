import yaml
import json
import kubernetes.client.models
import sys

class RecordWrapper:

    def __init__(self, data):
        self.data = data

class CmRecordBuilder:

    def __init__(self, api_client, core_type, data_types):
        self.api_client = api_client
        self.core_type = core_type
        for data_type_name, data_type in data_types.items():
            # Register our custom types on the Kubernetes model module so they can be deserialized by the client in Kubernetes module
            # Replace with our own generated client and/or deserializer
            setattr(sys.modules['kubernetes.client.models'], data_type_name, data_type)

    def to_record(self, orig_obj):
        obj_as_dict = self.api_client.sanitize_for_serialization(orig_obj)
        return yaml.safe_dump(obj_as_dict)

    def from_record(self, obj_as_dict_str):
        obj_as_dict = yaml.safe_load(obj_as_dict_str)
        obj_as_json = json.dumps(obj_as_dict)
        return self.api_client.deserialize(RecordWrapper(obj_as_json), self.core_type)
