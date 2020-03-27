from .exceptions import InvalidDeploymentLocationError
import pathlib
import yaml
import kubernetes.config as kubeconfig
import tempfile
from kubedriver.kubeclient import DEFAULT_NAMESPACE
    
def get_property_or_default(properties, *keys, default_provider=None, error_if_not_found=False):
    if len(keys) == 0:
        raise ValueError('Must provide at least one key to find property')
    value = None
    value_found = False
    for key in keys:
        if key in properties:
            value_found = True
            value = properties.get(key)
            break
    # Can't base this on value being not None as it may have been set to None deliberately
    if not value_found:
        if error_if_not_found:
            error_msg = 'Deployment location properties missing value for property \'{0}\''.format(keys[0])
            if len(keys) > 1:
                error_msg += ' (or: {0})'.format(keys[1:])
            raise InvalidDeploymentLocationError(error_msg)
        if callable(default_provider):
            return default_provider()
        else:
            return default_provider
    else:
        return value

class KubeDeploymentLocation:

    NAME = 'name'
    PROPERTIES = 'properties'
    CONFIG_PROP = 'clientConfig'
    CONFIG_OPT2_PROP = 'client_config'
    CRD_API_VERSION_PROP = 'crdApiVersion'
    CRD_API_VERSION_OPT2_PROP = 'crd_api_version'
    DRIVER_NAMESPACE_PROP = 'driverNamespace'
    DRIVER_NAMESPACE_OPT2_PROP = 'driver_namespace'
    CM_API_VERSION_PROP = 'cmApiVersion'
    CM_API_VERSION_OPT2_PROP = 'cm_api_version'
    CM_KIND_PROP = 'cmKind'
    CM_KIND_OPT2_PROP = 'cm_kind'
    CM_DATA_FIELD_PROP = 'cmDataField'
    CM_DATA_FIELD_OPT2_PROP = 'cm_data_field'
    DEFAULT_OBJECT_NAMESPACE_PROP = 'defaultObjectNamepsace'
    DEFAULT_OBJECT_NAMESPACE_OPT2_PROP = 'default_object_namespace'

    @staticmethod
    def from_dict(dl_data):
        name = dl_data.get(KubeDeploymentLocation.NAME, None)
        if name is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubeDeploymentLocation.NAME))
        properties = dl_data.get(KubeDeploymentLocation.PROPERTIES, None)
        if properties is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubeDeploymentLocation.PROPERTIES))
        client_config = get_property_or_default(properties, KubeDeploymentLocation.CONFIG_PROP, KubeDeploymentLocation.CONFIG_OPT2_PROP, error_if_not_found=True)
        if type(client_config) is str:
            client_config = yaml.safe_load(client_config)
        kwargs = {}
        crd_api_version = get_property_or_default(properties, KubeDeploymentLocation.CRD_API_VERSION_PROP, KubeDeploymentLocation.CRD_API_VERSION_OPT2_PROP)
        if crd_api_version is not None:
            kwargs['crd_api_version'] = crd_api_version
        driver_namespace = get_property_or_default(properties, KubeDeploymentLocation.DRIVER_NAMESPACE_PROP, KubeDeploymentLocation.DRIVER_NAMESPACE_OPT2_PROP)
        if driver_namespace is not None:
            kwargs['driver_namespace'] = driver_namespace
        cm_api_version = get_property_or_default(properties, KubeDeploymentLocation.CM_API_VERSION_PROP, KubeDeploymentLocation.CM_API_VERSION_OPT2_PROP)
        if cm_api_version is not None:
            kwargs['cm_api_version'] = cm_api_version
        cm_kind = get_property_or_default(properties, KubeDeploymentLocation.CM_KIND_PROP, KubeDeploymentLocation.CM_KIND_OPT2_PROP)
        if cm_kind is not None:
            kwargs['cm_kind'] = cm_kind
        cm_data_field = get_property_or_default(properties, KubeDeploymentLocation.CM_DATA_FIELD_PROP, KubeDeploymentLocation.CM_DATA_FIELD_OPT2_PROP)
        if cm_data_field is not None:
            kwargs['cm_data_field'] = cm_data_field
        default_object_namespace = get_property_or_default(properties, KubeDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_PROP, KubeDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_OPT2_PROP)
        if default_object_namespace is not None:
            kwargs['default_object_namespace'] = default_object_namespace
        return KubeDeploymentLocation(name, client_config, **kwargs)

    def __init__(self, name, client_config, default_object_namespace=DEFAULT_NAMESPACE, crd_api_version=None, driver_namespace=None, \
                    cm_api_version=None, cm_kind=None, cm_data_field=None):
        self.name = name
        self.client_config = client_config
        self.crd_api_version = crd_api_version
        self.driver_namespace = driver_namespace
        self.cm_api_version = cm_api_version
        self.cm_kind = cm_kind
        self.cm_data_field = cm_data_field
        self.default_object_namespace = default_object_namespace
        if self.driver_namespace is None:
            self.driver_namespace = self.default_object_namespace

    def build_client(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = pathlib.Path(tmpdir).joinpath('kubeconf.yaml')
            with open(tmp_file_path, 'w') as f:
                yaml.dump(self.client_config, f)
            client = kubeconfig.new_client_from_config(str(tmp_file_path), persist_config=False)
        return client

    def to_dict(self):
        return {
            KubeDeploymentLocation.NAME: self.name,
            KubeDeploymentLocation.PROPERTIES: {
                KubeDeploymentLocation.CONFIG_PROP: self.client_config,
                KubeDeploymentLocation.CRD_API_VERSION_PROP: self.crd_api_version,
                KubeDeploymentLocation.DRIVER_NAMESPACE_PROP: self.driver_namespace,
                KubeDeploymentLocation.CM_API_VERSION_PROP: self.cm_api_version,
                KubeDeploymentLocation.CM_KIND_PROP: self.cm_kind,
                KubeDeploymentLocation.CM_DATA_FIELD_PROP: self.cm_data_field,
                KubeDeploymentLocation.DEFAULT_OBJECT_NAMESPACE_PROP: self.default_object_namespace
            }
        }