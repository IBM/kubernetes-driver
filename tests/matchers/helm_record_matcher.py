from kubedriver.keg.records import HelmReleaseRecord

def helm_record(expected_record):
    return HelmReleaseRecordMatcher(expected_record)

class HelmReleaseRecordMatcher:

    def __init__(self, expected_record):
        self.expected_record = expected_record

    def __eq__(self, other):
        if not isinstance(other, HelmReleaseRecord):
            return False
        if other.chart != self.expected_record.chart:
            return False
        if other.name != self.expected_record.name:
            return False
        if other.namespace != self.expected_record.namespace:
            return False
        if other.values != self.expected_record.values:
            return False
        if other.state != self.expected_record.state:
            return False
        if other.error != self.expected_record.error:
            return False
        return True

    def __str__(self):
        return str(self.expected_record)

    def __repr__(self):
        return f'{self.expected_record!r}'
