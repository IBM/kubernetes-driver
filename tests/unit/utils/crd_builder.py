from kubedriver.kubeclient.defaults import DEFAULT_CRD_API_VERSION
#The "V1beta1" part of these has changed to "V1" in the latest release of the client
from kubernetes.client.models import (V1beta1CustomResourceDefinition, V1beta1CustomResourceDefinitionSpec, V1ObjectMeta,
                                        V1beta1CustomResourceDefinitionVersion, V1beta1CustomResourceDefinitionNames)


def build_crd(kind='MyCustom', singular='mycustom', plural='mycustoms', group='example.com', scope='Namespaced', versions=['v1']):
    versions_list = []
    for idx, version in enumerate(versions):
        served = False if idx != 0 else True
        storage = False if idx != 0 else True
        version_def = V1beta1CustomResourceDefinitionVersion(name=version, served=served, storage=storage)
        versions_list.append(version_def)
    spec = V1beta1CustomResourceDefinitionSpec(
        group=group, 
        names=V1beta1CustomResourceDefinitionNames(
            plural=plural,
            singular=singular,
            kind=kind
        ),
        scope=scope,
        versions=versions_list
    )
    crd = V1beta1CustomResourceDefinition(
        api_version=DEFAULT_CRD_API_VERSION,
        kind=kind,
        metadata=V1ObjectMeta(name=f'{plural}.{group}'),
        spec=spec
    )
    return crd