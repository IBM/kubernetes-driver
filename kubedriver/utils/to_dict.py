def to_dict(obj):
    result = {}
    if hasattr(obj, 'openapi_types'):
        attrs = obj.openapi_types.keys()
    elif hasattr(obj, 'dict_attrs'):
        attrs = obj.dict_attrs
    else:
        attrs = []
    if hasattr(obj, 'attribute_map'):
        alt_attr_names = obj.attribute_map
    else:
        alt_attr_names = {}
    for attr in attrs:
        value = getattr(obj, attr)
        if isinstance(value, list):
            result[attr] = []
            for e in value:
                if hasattr(e, 'to_dict'):
                    result[attr].append(e.to_dict())
                else:
                    result[attr].append(e)
        elif hasattr(value, 'to_dict'):
            result[attr] = value.to_dict()
        elif isinstance(value, dict):
            result[attr] = {}
            for k, v in value.items():
                if hasattr(v, 'to_dict'):
                    result[attr][k] = v.to_dict()
                else:
                    result[attr][k] = v
        else:
            result[attr] = value
    return result
