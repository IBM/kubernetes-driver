import yaml
import os
import kubernetes.config as kubeconfig
import ignition.locations.kubernetes as common_kube_dl
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ignition.locations.utils import get_property_or_default
from kubedriver.kubeclient import DEFAULT_NAMESPACE
from kubedriver.helmclient import HelmClient, HelmTls

KubeDeploymentLocationBase = common_kube_dl.KubernetesDeploymentLocation

class KubeDeploymentLocation(KubeDeploymentLocationBase):

    CRD_API_VERSION_PROP = 'crdApiVersion'
    CRD_API_VERSION_ALT2_PROP = 'crd_api_version'
    DRIVER_NAMESPACE_PROP = 'driverNamespace'
    DRIVER_NAMESPACE_ALT2_PROP = 'driver_namespace'
    CM_API_VERSION_PROP = 'cmApiVersion'
    CM_API_VERSION_ALT2_PROP = 'cm_api_version'
    CM_KIND_PROP = 'cmKind'
    CM_KIND_ALT2_PROP = 'cm_kind'
    CM_DATA_FIELD_PROP = 'cmDataField'
    CM_DATA_FIELD_ALT2_PROP = 'cm_data_field'

    #Helm
    HELM_VERSION_PROP = 'helmVersion'
    HELM_VERSION_ALT2_PROP = 'helm_version'
    HELM_VERSION_ALT3_PROP = 'helm.version'
    HELM_TLS_ENABLED_PROP = 'helm.tls.enabled'
    HELM_TLS_CA_CERT_PROP = 'helm.tls.cacert'
    HELM_TLS_CA_CERT_ALT2_PROP = 'helm.tls.ca_cert'
    HELM_TLS_CERT_PROP = 'helm.tls.cert'
    HELM_TLS_KEY_PROP = 'helm.tls.key' 

    @staticmethod
    def from_dict(dl_data):
        name = dl_data.get(KubeDeploymentLocationBase.NAME)
        if name is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubeDeploymentLocationBase.NAME))
        properties = dl_data.get(KubeDeploymentLocationBase.PROPERTIES)
        if properties is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubeDeploymentLocationBase.PROPERTIES))
        client_config = get_property_or_default(properties, KubeDeploymentLocationBase.CONFIG_PROP, KubeDeploymentLocationBase.CONFIG_ALT2_PROP, error_if_not_found=True)
        if type(client_config) is str:
            client_config = yaml.safe_load(client_config)
        kwargs = {}
        crd_api_version = get_property_or_default(properties, KubeDeploymentLocation.CRD_API_VERSION_PROP, KubeDeploymentLocation.CRD_API_VERSION_ALT2_PROP)
        if crd_api_version is not None:
            kwargs['crd_api_version'] = crd_api_version
        driver_namespace = get_property_or_default(properties, KubeDeploymentLocation.DRIVER_NAMESPACE_PROP, KubeDeploymentLocation.DRIVER_NAMESPACE_ALT2_PROP)
        if driver_namespace is not None:
            kwargs['driver_namespace'] = driver_namespace
        cm_api_version = get_property_or_default(properties, KubeDeploymentLocation.CM_API_VERSION_PROP, KubeDeploymentLocation.CM_API_VERSION_ALT2_PROP)
        if cm_api_version is not None:
            kwargs['cm_api_version'] = cm_api_version
        cm_kind = get_property_or_default(properties, KubeDeploymentLocation.CM_KIND_PROP, KubeDeploymentLocation.CM_KIND_ALT2_PROP)
        if cm_kind is not None:
            kwargs['cm_kind'] = cm_kind
        cm_data_field = get_property_or_default(properties, KubeDeploymentLocation.CM_DATA_FIELD_PROP, KubeDeploymentLocation.CM_DATA_FIELD_ALT2_PROP)
        if cm_data_field is not None:
            kwargs['cm_data_field'] = cm_data_field
        default_object_namespace = get_property_or_default(properties, KubeDeploymentLocationBase.DEFAULT_OBJECT_NAMESPACE_PROP, KubeDeploymentLocationBase.DEFAULT_OBJECT_NAMESPACE_ALT2_PROP)
        if default_object_namespace is not None:
            kwargs['default_object_namespace'] = default_object_namespace
        helm_version = get_property_or_default(properties, KubeDeploymentLocation.HELM_VERSION_PROP, KubeDeploymentLocation.HELM_VERSION_ALT2_PROP, KubeDeploymentLocation.HELM_VERSION_ALT3_PROP)
        if helm_version is not None:
            kwargs['helm_version'] = helm_version
        helm_tls_enabled = get_property_or_default(properties, KubeDeploymentLocation.HELM_TLS_ENABLED_PROP)
        if helm_tls_enabled is not None:
            if type(helm_tls_enabled) == str:
                helm_tls_enabled = helm_tls_enabled.lower() in ['True', 'true', 'yes', 't', 'y']
            if helm_tls_enabled:
                kwargs['helm_tls'] = HelmTls(enabled=True)
                kwargs['helm_tls'].ca_cert = get_property_or_default(properties, KubeDeploymentLocation.HELM_TLS_CA_CERT_PROP, KubeDeploymentLocation.HELM_TLS_CA_CERT_ALT2_PROP)
                kwargs['helm_tls'].cert = get_property_or_default(properties, KubeDeploymentLocation.HELM_TLS_CERT_PROP)
                kwargs['helm_tls'].key = get_property_or_default(properties, KubeDeploymentLocation.HELM_TLS_KEY_PROP)
        return KubeDeploymentLocation(name, client_config, **kwargs)

    def __init__(self, name, client_config, default_object_namespace=DEFAULT_NAMESPACE, crd_api_version=None, driver_namespace=None, \
                    cm_api_version='v1', cm_kind='ConfigMap', cm_data_field='data', helm_version='3.13.2', helm_tls=None):
        super().__init__(name, client_config, default_object_namespace=default_object_namespace)
        self.crd_api_version = crd_api_version
        self.cm_api_version = cm_api_version
        self.cm_kind = cm_kind
        self.cm_data_field = cm_data_field
        self.driver_namespace = driver_namespace
        if self.driver_namespace is None:
            self.driver_namespace = self.default_object_namespace
        self.helm_version = helm_version
        self.helm_tls = helm_tls
        self._client = None
        self._helm_client = None

    @property
    def client(self):
        if self._client is None:
            config_file_path = super().write_config_file()
            try:
                self._client = kubeconfig.new_client_from_config(config_file_path, persist_config=False)            
            finally:
                if os.path.exists(config_file_path):
                    os.remove(config_file_path)
        return self._client

    @property
    def helm_client(self):
        if self._helm_client is None:
            self._helm_client = HelmClient(self.client_config, self.helm_version, tls=self.helm_tls)
        return self._helm_client

    def clean(self):
        self.clear_config_files()
        if self._helm_client is not None:
            self._helm_client.close()
            self._helm_client = None

    def get_cm_persister_args(self):
        args = {}
        if self.cm_api_version is not None:
            args['cm_api_version'] = self.cm_api_version
        if self.cm_kind is not None:
            args['cm_kind'] = self.cm_kind
        if self.cm_data_field is not None:
            args['cm_data_field'] = self.cm_data_field
        return args
        
    def to_dict(self):
        data = super().to_dict()
        data[KubeDeploymentLocationBase.PROPERTIES].update({
            KubeDeploymentLocation.CRD_API_VERSION_PROP: self.crd_api_version,
            KubeDeploymentLocation.DRIVER_NAMESPACE_PROP: self.driver_namespace,
            KubeDeploymentLocation.CM_API_VERSION_PROP: self.cm_api_version,
            KubeDeploymentLocation.CM_KIND_PROP: self.cm_kind,
            KubeDeploymentLocation.CM_DATA_FIELD_PROP: self.cm_data_field,
            KubeDeploymentLocation.HELM_VERSION_PROP: self.helm_version,
            KubeDeploymentLocation.HELM_TLS_ENABLED_PROP: self.helm_tls.enabled if self.helm_tls is not None else None,
            KubeDeploymentLocation.HELM_TLS_CA_CERT_PROP: self.helm_tls.ca_cert if self.helm_tls is not None else None,
            KubeDeploymentLocation.HELM_TLS_CERT_PROP: self.helm_tls.cert if self.helm_tls is not None else None,
            KubeDeploymentLocation.HELM_TLS_KEY_PROP: self.helm_tls.key if self.helm_tls is not None else None,
        })
        return data
