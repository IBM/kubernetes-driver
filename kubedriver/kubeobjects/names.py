import re

NAME_REGEX = re.compile('[^a-z0-9.-]+')
REPEATED_SEPARATOR_REGEX = re.compile('(?P<sep>['+re.escape('-.')+'])(?P=sep)')
MAX_NAME_LENGTH = 253

class NameHelper:

    def safe_subdomain_name(self, input_name):
        if input_name is None:
            raise ValueError('input_name cannot be None')
        ## Names must be lowercase
        potential_name = input_name.lower()
        ## Replace spaces and underscores (a common separator char) with valid separator char dash ('-')
        potential_name = potential_name.replace(' ', '-')
        potential_name = potential_name.replace('_', '-')
        ## Remove any remaining non valid characters (anything that is not a lowercase letter, number, dot or dash)
        potential_name = NAME_REGEX.sub('', potential_name)
        if len(potential_name) == 0:
            raise ValueError('Converting name \'{0}\' to a Kubernetes safe name results in an empty string'.format(input_name))
        ## If we have duplicate dots or dashes, reduce them to a single character
        potential_name = REPEATED_SEPARATOR_REGEX.sub(r'\1', potential_name)
        ## Ensure the name starts with an alphanumeric value
        ## Remove each non-alphanumeric char from the start until we hit one
        while not potential_name[0].isalnum():
            if len(potential_name) == 1:
                raise ValueError('Converting name \'{0}\' to a Kubernetes safe name results in a string containing only non-alphanumeric characters (must start with alphanumeric). Current potential name when error raised: \'{1}\''.format(input_name, potential_name))
            potential_name = potential_name[1:]
        ## Trim the name until it fits under the max length
        if len(potential_name) > MAX_NAME_LENGTH: 
            potential_name = potential_name[0:MAX_NAME_LENGTH]
        ## Ensure name ends with an alphanumeric value
        ## Remove each non-alphanumeric char from the end until we hit one
        ## (this shouldn't be possible as we've stripped alpha numeric from the front so we'll have at least one character)
        while not potential_name[-1].isalnum():
            if len(potential_name) == 1:
                raise ValueError('Converting name \'{0}\' to a Kubernetes safe name results in a string containing only non-alphanumeric characters (must end with alphanumeric). Current potential name when error raised: \'{1}\''.format(input_name, potential_name))
            potential_name = potential_name[:-1]
        return potential_name