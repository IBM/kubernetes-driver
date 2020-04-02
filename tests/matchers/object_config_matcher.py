from kubedriver.kubeobjects import ObjectConfiguration

def object_config(expected_raw_config):
    return ObjectConfigurationMatcher(expected_raw_config)


class ObjectConfigurationMatcher:

    def __init__(self, expected_raw_conf):
        self.expected_config = ObjectConfiguration(expected_raw_conf)

    def __eq__(self, other):
        return other.data == self.expected_config.data

    def __str__(self):
        return str(self.expected_config)

    def __repr__(self):
        return f'{self.expected_config!r}'
