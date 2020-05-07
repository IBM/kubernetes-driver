from kubedriver.keg.records import ObjectRecord

def object_record(expected_record):
    return ObjectRecordMatcher(expected_record)

class ObjectRecordMatcher:

    def __init__(self, expected_record):
        self.expected_record = expected_record

    def __eq__(self, other):
        if not isinstance(other, ObjectRecord):
            return False
        if other.config != self.expected_record.config:
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
