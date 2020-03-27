import unittest
import json
from kubernetes.client.rest import ApiException
from kubedriver.kubeclient.error_reader import ErrorReader

class MockHttpResponse:

    def __init__(self, status=None, reason=None, data=None, headers=None):
        self.status = status
        self.reason = reason
        self.data = data
        self.headers = headers

    def getheaders(self):
        return self.headers

def json_body(body):
    return json.dumps(body)

class TestErrorReader(unittest.TestCase):

    def setUp(self):
        self.error_reader = ErrorReader()

    def __test(self, func, valid_status, valid_reason, valid_body_reason=None):
        valid_body = json_body({'reason': valid_body_reason})
        # Check matching error
        valid_error = ApiException(http_resp=MockHttpResponse(status=valid_status, reason=valid_reason, data=valid_body))
        self.assertTrue(func(valid_error))
        # Incorrect Status
        error_with_incorrect_status = ApiException(http_resp=MockHttpResponse(status=valid_status+1, reason=valid_reason, data=valid_body))
        self.assertFalse(func(error_with_incorrect_status))
        # Incorrect Reason
        error_with_incorrect_reason = ApiException(http_resp=MockHttpResponse(status=valid_status, reason='Some reason', data=valid_body))
        self.assertFalse(func(error_with_incorrect_reason))
        # Invalid Body
        error_with_invalid_body = ApiException(http_resp=MockHttpResponse(status=valid_status, reason=valid_reason, data='Some reason'))
        self.assertFalse(func(error_with_invalid_body))
        # Incorrect Body Reason
        error_with_incorrect_reason_in_body = ApiException(http_resp=MockHttpResponse(status=valid_status, reason=valid_reason, data=json_body({'reason': 'Some reason'})))
        self.assertFalse(func(error_with_incorrect_reason_in_body))

    def test_is_already_exists_err(self):
        self.__test(self.error_reader.is_already_exists_err, 409, 'Conflict', valid_body_reason='AlreadyExists')

    def test_is_not_found_err(self):
        self.__test(self.error_reader.is_not_found_err, 404, 'Not Found', valid_body_reason='NotFound')
        