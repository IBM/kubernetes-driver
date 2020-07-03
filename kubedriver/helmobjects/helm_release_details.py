import pprint 
from kubedriver.utils.to_dict import to_dict

class HelmReleaseDetails:
    openapi_types = {
        'name': 'str',
        'namespace': 'str',
        'revision': 'int',
        'released': 'str',
        'chart': 'str',
        'user_supplied_values': 'dict',
        'computed_values': 'dict',
        'manifest': 'dict',
        'last_deployed': 'str',
        'status': 'str'
    }

    attribute_map = {
        'name': 'name',
        'namespace': 'namespace',
        'revision': 'revision',
        'released': 'released',
        'chart': 'chart',
        'user_supplied_values': 'userSuppliedValues',
        'computed_values': 'computedValues',
        'manifest': 'manifest',
        'last_deployed': 'lastDeployed',
        'status': 'status'
    }
    def __init__(self, name=None, namespace=None, revision=None, released=None, chart=None, user_supplied_values=None, computed_values=None, manifest=None, last_deployed=None, status=None):
        self._name = name
        self._namespace = namespace
        self._revision = revision
        self._released = released
        self._chart = chart
        self._user_supplied_values = user_supplied_values
        self._computed_values = computed_values
        self._manifest = manifest
        self._last_deployed = last_deployed
        self._status = status


    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        self._namespace = namespace

    @property
    def revision(self):
        return self._revision

    @revision.setter
    def revision(self, revision):
        self._revision = revision

    @property
    def released(self):
        return self._released

    @released.setter
    def released(self, released):
        self._released = released

    @property
    def chart(self):
        return self._chart

    @chart.setter
    def chart(self, chart):
        self._chart = chart

    @property
    def user_supplied_values(self):
        return self._user_supplied_values

    @user_supplied_values.setter
    def user_supplied_values(self, user_supplied_values):
        self._user_supplied_values = user_supplied_values

    @property
    def computed_values(self):
        return self._computed_values

    @computed_values.setter
    def computed_values(self, computed_values):
        self._computed_values = computed_values

    @property
    def manifest(self):
        return self._manifest

    @manifest.setter
    def manifest(self, manifest):
        self._manifest = manifest

    @property
    def last_deployed(self):
        return self._last_deployed

    @last_deployed.setter
    def last_deployed(self, last_deployed):
        self._last_deployed = last_deployed

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, HelmReleaseDetails):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
