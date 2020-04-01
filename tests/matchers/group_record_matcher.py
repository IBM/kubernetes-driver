from .object_record_matcher import ObjectRecordMatcher
from .request_record_matcher import RequestRecordMatcher
from .helm_record_matcher import HelmRecordMatcher
from kubedriver.manager.records import GroupRecord

def group_record(expected_group_record):
    return GroupRecordMatcher(expected_group_record)

class GroupRecordMatcher:

    def __init__(self, expected_group_record):
        self.expected_group_record = expected_group_record

    def __eq__(self, other):
        if not isinstance(other, GroupRecord):
            return False
        if other.uid != self.expected_group_record.uid:
            return False
        if len(other.objects) != len(self.expected_group_record.objects):
            return False
        for idx in range(len(other.objects)):
            if ObjectRecordMatcher(other.objects[idx]) != self.expected_group_record.objects[idx]:
                return False
        if len(other.requests) != len(self.expected_group_record.requests):
            return False
        for idx in range(len(other.requests)):
            if RequestRecordMatcher(other.requests[idx]) != self.expected_group_record.requests[idx]:
                return False
        if len(other.helm_releases) != len(self.expected_group_record.helm_releases):
            return False
        for idx in range(len(other.helm_releases)):
            if HelmRecordMatcher(other.helm_releases[idx]) != self.expected_group_record.helm_releases[idx]:
                return False
        return True

    def __str__(self):
        return str(self.expected_group_record)

    def __repr__(self):
        return f'{self.expected_group_record!r}'
