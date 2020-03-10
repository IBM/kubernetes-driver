from .exceptions import InvalidDeploymentLocationError
import pathlib
import yaml
import kubernetes.config as kubeconfig
import tempfile

class KubernetesDeploymentLocation:

    NAME = 'name'
    PROPERTIES = 'properties'
    CONFIG = 'clientConfig'
    CONFIG_OPT2 = 'client_config'

    @staticmethod
    def from_dict(dl_data):
        name = dl_data.get(KubernetesDeploymentLocation.NAME, None)
        if name is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubernetesDeploymentLocation.NAME))
        properties = dl_data.get(KubernetesDeploymentLocation.PROPERTIES, None)
        if properties is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'{0}\' value'.format(KubernetesDeploymentLocation.PROPERTIES))
        client_config = properties.get(KubernetesDeploymentLocation.CONFIG, None)
        if client_config is None:
            client_config = properties.get(KubernetesDeploymentLocation.CONFIG_OPT2, None)
            if client_config is None:
                raise InvalidDeploymentLocationError('Deployment location properties missing \'{0}\' or \'{1}\' value'.format(KubernetesDeploymentLocation.CONFIG, KubernetesDeploymentLocation.CONFIG_OPT2))
        return KubernetesDeploymentLocation(name, client_config)

    def __init__(self, name, client_config):
        self.name = name
        self.client_config = client_config

    def build_client(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file_path = pathlib.Path(tmpdir).joinpath('kubeconf')
            with open(tmp_file_path, 'w') as f:
                yaml.dump(self.client_config, f)
            client = kubeconfig.new_client_from_config(str(tmp_file_path), persist_config=False)
        return client