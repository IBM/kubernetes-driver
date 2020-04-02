from kubedriver.kubegroup.records import RequestRecord

def request_record(expected_record):
    return RequestRecordMatcher(expected_record)

class RequestRecordMatcher:

    def __init__(self, expected_record):
        self.expected_record = expected_record

    def __eq__(self, other):
        if not isinstance(other, RequestRecord):
            return False
        if other.uid != self.expected_record.uid:
            return False
        if other.operation != self.expected_record.operation:
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
