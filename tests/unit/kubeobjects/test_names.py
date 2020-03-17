import unittest
from kubedriver.kubeobjects.names import NameHelper

class TestNameHelper(unittest.TestCase):

    def setUp(self):
        self.helper = NameHelper()

    def test_safe_subdomain_name_removes_uppercase(self):
        self.assertEqual(self.helper.safe_subdomain_name('TestingUppercase'), 'testinguppercase')

    def test_safe_subdomain_name_replaces_underscore(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing_underscore'), 'testing-underscore')

    def test_safe_subdomain_name_replaces_spaces(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing spaces'), 'testing-spaces')

    def test_safe_subdomain_name_allows_dots(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing.dots'), 'testing.dots')

    def test_safe_subdomain_name_allows_dashes(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing-dashes'), 'testing-dashes')

    def test_safe_subdomain_name_removes_special_chars(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing$@:;!?()-*&^%£"#specials'), 'testing-specials')

    def test_safe_subdomain_name_removes_repeated_dashes(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing--duplicate--dashes'), 'testing-duplicate-dashes')
        self.assertEqual(self.helper.safe_subdomain_name('testing-duplicate--dashes'), 'testing-duplicate-dashes')

    def test_safe_subdomain_name_removes_repeated_dots(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing..duplicate..dots'), 'testing.duplicate.dots')
        self.assertEqual(self.helper.safe_subdomain_name('testing..duplicate.dots'), 'testing.duplicate.dots')

    def test_safe_subdomain_name_raises_error_if_replacements_cause_empty_string(self):
        with self.assertRaises(ValueError) as context:
            self.helper.safe_subdomain_name('$@!')
        self.assertEqual(str(context.exception), 'Converting name \'$@!\' to a Kubernetes safe name results in an empty string')

    def test_safe_subdomain_name_ensures_alphanumeric_at_start(self):
        self.assertEqual(self.helper.safe_subdomain_name('-testing-nonalpha'), 'testing-nonalpha')
    
    def test_safe_subdomain_name_ensures_alphanumeric_at_end(self):
        self.assertEqual(self.helper.safe_subdomain_name('testing-nonalpha-'), 'testing-nonalpha')

    def test_safe_subdomain_name_raises_error_if_search_for_alphanumeric_start_causes_empty_string(self):
        with self.assertRaises(ValueError) as context:
            self.helper.safe_subdomain_name('--.--')
        self.assertEqual(str(context.exception), 'Converting name \'--.--\' to a Kubernetes safe name results in a string containing only non-alphanumeric characters (must start with alphanumeric). Current potential name when error raised: \'-\'')

    def test_safe_subdomain_name_reduces_length(self):
        self.assertEqual(self.helper.safe_subdomain_name(254*'a'), 253*'a')

    def test_safe_subdomain_name_ensures_alphanumeric_at_end_after_reducing_length(self):
        self.assertEqual(self.helper.safe_subdomain_name(253*'a' + '-'), 253*'a')
        self.assertEqual(self.helper.safe_subdomain_name(252*'a' + '-a'), 252*'a')
