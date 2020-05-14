import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1KegdStrategyReportStatus(object):

    openapi_types = {
        'uid': 'str',
        'keg_name': 'str',
        'operation': 'str',
        'task_groups': 'list[str]',
        'run_cleanup': 'bool',
        'state': 'str',
        'phase': 'str',
        'errors': 'list[str]', 
        'outputs': 'dict(str, str)'
    }

    attribute_map = {
        'uid': 'uid',
        'keg_name': 'kegName',
        'operation': 'operation',
        'task_groups': 'taskGroups',
        'run_cleanup': 'runCleanup',
        'state': 'state',
        'phase': 'phase',
        'errors': 'errors',
        'outputs': 'outputs'
    }

    def __init__(self, uid=None, keg_name=None, operation=None, task_groups=None, run_cleanup=None, state=None, phase=None, errors=None, outputs=None):
        self._uid = uid
        self._keg_name = keg_name
        self._operation = operation
        self._task_groups = task_groups
        self._run_cleanup = run_cleanup
        self._state = state
        self._phase = phase
        self._errors = errors
        self._outputs = outputs

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    @property
    def keg_name(self):
        return self._keg_name

    @keg_name.setter
    def keg_name(self, keg_name):
        self._keg_name = keg_name

    @property
    def operation(self):
        return self._operation

    @operation.setter
    def operation(self, operation):
        self._operation = operation
    
    @property
    def task_groups(self):
        return self._task_groups

    @task_groups.setter
    def task_groups(self, task_groups):
        self._task_groups = task_groups
    
    @property
    def run_cleanup(self):
        return self._run_cleanup

    @run_cleanup.setter
    def run_cleanup(self, run_cleanup):
        self._run_cleanup = run_cleanup

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, phase):
        self._phase = phase

    @property
    def errors(self):
        return self._errors

    @errors.setter
    def errors(self, errors):
        self._errors = errors

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1KegdStrategyReportStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other