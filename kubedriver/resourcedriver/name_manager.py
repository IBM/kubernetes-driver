from kubedriver.kubeobjects import namehelper
from ignition.service.framework import Service, Capability
import re

REMOVE_SUBDOMAIN_INVALID_REGEX = re.compile('[^a-z0-9.-]+')
REPEATED_SUBDOMAIN_SEPARATOR_REGEX = re.compile('(?P<sep>['+re.escape('-.')+'])(?P=sep)')
REMOVE_LABEL_INVALID_REGEX = re.compile('[^a-z0-9-]+')
REPEATED_LABEL_SEPARATOR_REGEX = re.compile('(?P<sep>['+re.escape('-')+'])(?P=sep)')
REMOVE_VOWEL_REGEX = re.compile('[aeiouAEIOU]')

## Care should be taken when updating this class as any changes to name generation could mean we are left 
## with instances that cannot be uninstalled (because we now generate a different name for it)

class NameManager(Service, Capability):

    def __execute_attempts(self, attempts, validator, error_title):
        attempt_errors = []
        valid = False
        result = None
        previous_attempts = []
        for attempt in attempts:
            if callable(attempt):
                result = attempt()
            elif type(attempt) == str:
                result = attempt
            else:
                raise ValueError(f'Attempt must be callable or a str but was {type(attempt)}')
            if result is not None and result not in previous_attempts:
                previous_attempts.append(result)
                valid, invalid_reason = validator(result)
                if not valid:
                    attempt_errors.append(f'Attempt \'{result}\' was invalid: {invalid_reason}')
                else:
                    break
        if not valid:
            raise ValueError(f'Failed to generate {error_title}: {attempt_errors}')
        else:
            return result

    def safe_label_name_from_resource_id(self, resource_id):
        attempts = [
            lambda: self.__make_safe_label(resource_id)
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_label_name, 'safe label name from Resource ID')

    def safe_label_name_from_resource_name(self, resource_name):
        attempts = [
            lambda: self.__make_safe_label(resource_name),
            lambda: self.__make_safe_label(self.__short_resource_name(resource_name)),
            lambda: self.__make_safe_label(self.__short_resource_name_reduced(resource_name))
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_label_name, 'safe label name from Resource name')

    def safe_label_name_for_resource(self, resource_id, resource_name, prefix=None):
        if prefix == None:
            prefix = ''
        else:
            prefix = prefix + '-'
        attempts = [
            lambda: self.__make_safe_label(f'{prefix}{resource_name}-{resource_id}'),
            lambda: self.__make_safe_label(f'{prefix}{self.__short_resource_name(resource_name)}-{resource_id}'),
            lambda: self.__make_safe_label(f'{prefix}{self.__short_resource_name_reduced(resource_name)}-{resource_id}'),
            lambda: self.__make_safe_label(f'{prefix}-{resource_id}')
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_label_name, 'safe label name for Resource')

    def safe_subdomain_name_from_resource_id(self, resource_id):
        attempts = [
            lambda: self.__make_safe_subdomain(resource_id)
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_subdomain_name, 'safe subdomain name from Resource ID')

    def safe_subdomain_name_from_resource_name(self, resource_name):
        attempts = [
            lambda: self.__make_safe_subdomain(resource_name),
            lambda: self.__make_safe_subdomain(self.__short_resource_name(resource_name)),
            lambda: self.__make_safe_subdomain(self.__short_resource_name_reduced(resource_name))
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_subdomain_name, 'safe subdomain name from Resource name')

    def safe_subdomain_name_for_resource(self, resource_id, resource_name):
        attempts = [
            lambda: self.__make_safe_subdomain(f'{resource_name}-{resource_id}'),
            lambda: self.__make_safe_subdomain(f'{self.__short_resource_name(resource_name)}-{resource_id}'),
            lambda: self.__make_safe_subdomain(f'{self.__short_resource_name_reduced(resource_name)}-{resource_id}'),
            lambda: self.__make_safe_label(f'{resource_id}')
        ]
        return self.__execute_attempts(attempts, namehelper.is_valid_subdomain_name, 'safe subdomain name for Resource')

    def __short_resource_name(self, resource_name):
        ##Build name with first and last parts
        split_parts = resource_name.split('__')
        short_resource_name = split_parts[0]
        if len(split_parts) > 1:
            short_resource_name += f'-{split_parts[-1]}'
        return short_resource_name

    def __short_resource_name_reduced(self, resource_name):
        ##Build name with first and last parts
        split_parts = resource_name.split('__')
        first_part = split_parts[0]
        last_part = None
        if len(split_parts) > 1:
            last_part = split_parts[-1]
        ##Reduce
        first_part_reduced = self.__remove_vowels_or_reduce_to_three_chars(first_part)
        if last_part is not None:
            last_part_reduced = self.__remove_vowels_or_reduce_to_three_chars(last_part)
            return f'{first_part_reduced}-{last_part_reduced}'
        else:
            return first_part_reduced

    def __remove_vowels(self, input_str):
        reduced_input = REMOVE_VOWEL_REGEX.sub('', input_str)
        # Only contained vowels, don't let this be used
        if len(reduced_input) == 0:
            return False, input_str
        # No vowels
        if len(reduced_input) == len(input_str):
            return False, input_str
        return True, reduced_input

    def __reduce_to_three_chars(self, input_str):
        if len(input_str) > 3:
            first_char = input_str[0]
            #Exact for odd length strings, rough middle for even length
            middle_char = input_str[int(len(input_str)/2)]
            last_char = input_str[-1]
            reduced_input = first_char + middle_char + last_char
            return True, reduced_input
        else:
            #Return the original
            return False, input_str

    def __remove_vowels_or_reduce_to_three_chars(self, input_str):
        has_reduced, reduced_input = self.__remove_vowels(input_str)
        if not has_reduced:
            _, reduced_input = self.__reduce_to_three_chars(input_str)
        return reduced_input

    def __make_safe_subdomain(self, input_name):
        if input_name is None:
            return None
        ## Subdomain names must be lowercase
        sdname = input_name.lower()
        ## Replace spaces and underscores (common separator chars) with valid separator char dash ('-')
        sdname = sdname.replace(' ', '-')
        sdname = sdname.replace('_', '-')
        ## Remove any remaining non valid characters (anything that is not a lowercase letter, number, dot or dash)
        sdname = REMOVE_SUBDOMAIN_INVALID_REGEX.sub('', sdname)
        ## If we have duplicate dots or dashes, reduce them to a single character
        sdname = REPEATED_SUBDOMAIN_SEPARATOR_REGEX.sub(r'\1', sdname)
        return sdname

    def __make_safe_label(self, input_name):
        if input_name is None:
            return None
        ## Labels names must be lowercase
        label = input_name.lower()
        ## Replace spaces, underscores and dots (common separator chars) with valid separator char dash ('-')
        label = label.replace(' ', '-')
        label = label.replace('_', '-')
        label = label.replace('.', '-')
        ## Remove any remaining non valid characters (anything that is not a lowercase letter, number or dash)
        label = REMOVE_LABEL_INVALID_REGEX.sub('', label)
        ## If we have duplicate dashes, reduce them to a single character
        label = REPEATED_LABEL_SEPARATOR_REGEX.sub(r'\1', label)
        return label