import unittest
from kubedriver.kubeobjects.names import NameHelper

class TestNameHelper(unittest.TestCase):

    def setUp(self):
        self.helper = NameHelper()

    def test_is_valid_subdomain_name_allows_lowercase(self):
        valid, reason = self.helper.is_valid_subdomain_name('testing')
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_subdomain_name_false_on_uppercase(self):
        valid, reason = self.helper.is_valid_subdomain_name('tESting')
        self.assertEqual(reason, 'Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid at index 1\']')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_allows_dots(self):
        valid, reason = self.helper.is_valid_subdomain_name('testing.dots')
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_subdomain_name_allows_dash(self):
        valid, reason = self.helper.is_valid_subdomain_name('testing-dashes')
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_subdomain_name_false_on_non_alphanumeric_start(self):
        valid, reason = self.helper.is_valid_subdomain_name('-non-alphanum-start')
        self.assertEqual(reason, 'Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid start\']')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_false_on_non_alphanumeric_end(self):
        valid, reason = self.helper.is_valid_subdomain_name('non-alphanum-end-')
        self.assertEqual(reason, 'Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid at index 16\']')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_false_on_special_character(self):
        valid, reason = self.helper.is_valid_subdomain_name('testing@specialchars')
        self.assertEqual(reason, 'Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\' -> [\'Invalid at index 7\']')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_false_on_exceed_max_length(self):
        test_str = 'a' * 254
        valid, reason = self.helper.is_valid_subdomain_name(test_str)
        self.assertEqual(reason, 'Subdomain names must contain no more than 253 characters -> Contained 254')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_allows_string_at_max_length(self):
        test_str = 'a' * 253
        valid, reason = self.helper.is_valid_subdomain_name(test_str)
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_subdomain_name_false_on_none(self):
        valid, reason = self.helper.is_valid_subdomain_name(None)
        self.assertEqual(reason, 'Subdomains cannot be empty')
        self.assertFalse(valid)

    def test_is_valid_subdomain_name_false_on_empty_string(self):
        valid, reason = self.helper.is_valid_subdomain_name('')
        self.assertEqual(reason, 'Subdomains cannot be empty')
        self.assertFalse(valid)

    def test_is_valid_label_name_allows_lowercase(self):
        valid, reason = self.helper.is_valid_label_name('testing')
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_label_name_false_on_uppercase(self):
        valid, reason = self.helper.is_valid_label_name('tESting')
        self.assertEqual(reason, 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\' -> [\'Invalid at index 1\']')
        self.assertFalse(valid)

    def test_is_valid_label_name_false_on_dots(self):
        valid, reason = self.helper.is_valid_label_name('testing.dots')
        self.assertEqual(reason, 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\' -> [\'Invalid at index 7\']')
        self.assertFalse(valid)

    def test_is_valid_label_name_allows_dash(self):
        valid, reason = self.helper.is_valid_label_name('testing-dashes')
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_label_name_false_on_non_alphanumeric_start(self):
        valid, reason = self.helper.is_valid_label_name('-non-alphanum-start')
        self.assertEqual(reason, 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\' -> [\'Invalid start\']')
        self.assertFalse(valid)

    def test_is_valid_label_name_false_on_non_alphanumeric_end(self):
        valid, reason = self.helper.is_valid_label_name('non-alphanum-end-')
        self.assertEqual(reason, 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\' -> [\'Invalid at index 16\']')
        self.assertFalse(valid)

    def test_is_valid_label_name_false_on_special_character(self):
        valid, reason = self.helper.is_valid_label_name('testing@specialchars')
        self.assertEqual(reason, 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\' -> [\'Invalid at index 7\']')
        self.assertFalse(valid)

    def test_is_valid_label_name_false_on_exceed_max_length(self):
        test_str = 'a' * 64
        valid, reason = self.helper.is_valid_label_name(test_str)
        self.assertEqual(reason, 'Label names must contain no more than 63 characters -> Contained 64')
        self.assertFalse(valid)

    def test_is_valid_label_name_allows_string_at_max_length(self):
        test_str = 'a' * 63
        valid, reason = self.helper.is_valid_label_name(test_str)
        self.assertIsNone(reason)
        self.assertTrue(valid)

    def test_is_valid_label_name_false_on_none(self):
        valid, reason = self.helper.is_valid_label_name(None)
        self.assertEqual(reason, 'Label names cannot be empty')
        self.assertFalse(valid)

    def test_is_valid_label_name_false_on_empty_string(self):
        valid, reason = self.helper.is_valid_label_name('')
        self.assertEqual(reason, 'Label names cannot be empty')
        self.assertFalse(valid)
