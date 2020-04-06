from kubedriver.kubeobjects import namehelper
import re

REMOVE_SUBDOMAIN_INVALID_REGEX = re.compile('[^a-z0-9.-]+')
REPEATED_SUBDOMAIN_SEPARATOR_REGEX = re.compile('(?P<sep>['+re.escape('-.')+'])(?P=sep)')
REMOVE_LABEL_INVALID_REGEX = re.compile('[^a-z0-9-]+')
REPEATED_LABEL_SEPARATOR_REGEX = re.compile('(?P<sep>['+re.escape('-')+'])(?P=sep)')
REMOVE_VOWEL_REGEX = re.compile('[aeiouAEIOU]')

class NameManager:

    def safe_label_name_for_resource(self, resource_id, resource_name):
        attempts = [self.__simple_join_attempt, self.__short_resource_name_attempt, self.__short_resource_name_without_vowels_attempt]
        attempt_errors = []
        valid = False
        label = None
        for attempt in attempts:
            input_name = attempt(resource_id, resource_name)
            label = self.__make_safe_label(input_name)
            valid, invalid_reason = namehelper.is_valid_label_name(label)
            if not valid:
                attempt_errors.append(f'Attempt {input_name} was invalid: {invalid_reason}')
            else:
                break
        if not valid:
            raise ValueError(f'Failed to generate safe label name for Resource {str(resource_name)}-{str(resource_id)}: {attempt_errors}')
        else:
            return label

    def safe_subdomain_name_for_resource(self, resource_id, resource_name):
        attempts = [self.__simple_join_attempt, self.__short_resource_name_attempt, self.__short_resource_name_without_vowels_attempt]
        attempt_errors = []
        valid = False
        sdname = None
        for attempt in attempts:
            input_name = attempt(resource_id, resource_name)
            sdname = self.__make_safe_subdomain(input_name)
            valid, invalid_reason = namehelper.is_valid_subdomain_name(sdname)
            if not valid:
                attempt_errors.append(f'Attempt {input_name} was invalid: {invalid_reason}')
            else:
                break
        if not valid:
            raise ValueError(f'Failed to generate safe subdomain name for Resource {str(resource_name)}-{str(resource_id)}: {attempt_errors}')
        else:
            return sdname

    def __simple_join_attempt(self, resource_id, resource_name):
        return f'{resource_name}-{resource_id}'

    def __short_resource_name_attempt(self, resource_id, resource_name):
        short_resource_name = self.__short_resource_name(resource_name)
        return f'{short_resource_name}-{resource_id}'

    def __short_resource_name_without_vowels_attempt(self, resource_id, resource_name):
        short_resource_name = self.__short_resource_name_without_vowels(resource_name)
        return f'{short_resource_name}-{resource_id}'

    def __short_resource_name(self, resource_name):
        ##Build name with first and last parts
        split_parts = resource_name.split('__')
        short_resource_name = split_parts[0]
        if len(split_parts) > 1:
            short_resource_name += f'-{split_parts[-1]}'
        return short_resource_name

    def __short_resource_name_without_vowels(self, resource_name):
        ##Build name with first and last parts
        short_resource_name = self.__short_resource_name(resource_name)
        ##Then remove vowels
        return REMOVE_VOWEL_REGEX.sub('', short_resource_name)

    def __make_safe_subdomain(self, input_name):
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