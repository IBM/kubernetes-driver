import re

MAX_SUBDOMAIN_NAME_LENGTH = 253
SUBDOMAIN_REGEX = re.compile('[a-z0-9]([-.a-z0-9]*[a-z0-9])?')
MAX_LABEL_NAME_LENGTH = 63
LABEL_REGEX = re.compile('[a-z0-9]([-a-z0-9]*[a-z0-9])?')
SUBDOMAIN_INVALID_REASON_BASIC = 'Subdomain names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters, \'-\' or \'.\''
LABEL_INVALID_REASON_BASIC = 'Label names must start and end with an alphanumeric character and consist of only lower case alphanumeric characters or \'-\''

class NameHelper:


    def is_valid_subdomain_name(self, name):
        if name is None:
            return False, 'Subdomains cannot be empty'
        if len(name) == 0: 
            return False, 'Subdomains cannot be empty'
        match = SUBDOMAIN_REGEX.match(name)
        offences = []
        if match is None:
            offences.append('Invalid start')
        else:
            if match.start() != 0:
                offences.append('Invalid start')
            if match.end() != len(name):
                offences.append(f'Invalid at index {match.end()}')
        if len(offences) > 0:
            reason = SUBDOMAIN_INVALID_REASON_BASIC
            reason += f' -> {offences}'
            return False, reason
        if len(name) > MAX_SUBDOMAIN_NAME_LENGTH:
            return False, f'Subdomain names must contain no more than {MAX_SUBDOMAIN_NAME_LENGTH} characters -> Contained {len(name)}'
        return True, None

    def is_valid_label_name(self, name):
        if name is None:
            return False, 'Label names cannot be empty'
        if len(name) == 0: 
            return False, 'Label names cannot be empty'
        match = LABEL_REGEX.match(name)
        offences = []
        if match is None:
            offences.append('Invalid start')
        else:
            if match.start() != 0:
                offences.append('Invalid start')
            if match.end() != len(name):
                offences.append(f'Invalid at index {match.end()}')
        if len(offences) > 0:
            reason = LABEL_INVALID_REASON_BASIC
            reason += f' -> {offences}'
            return False, reason
        if len(name) > MAX_LABEL_NAME_LENGTH:
            return False, f'Label names must contain no more than {MAX_LABEL_NAME_LENGTH} characters -> Contained {len(name)}'
        return True, None

helper = NameHelper()