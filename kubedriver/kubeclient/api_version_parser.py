
EXTENSIONS_GROUP_SUFFIX = '.k8s.io'
CORE_GROUP = 'core'

class ApiVersionParser:

    def parse(self, api_version):
        # apiVersion: v1 -> group=core, version=v1
        # apiVersion: apiextensions.k8s.io/v1beta1 -> group = apiextensions.k8s.io, version = v1beta1
        group, slash, version = api_version.partition('/')
        if len(version) == 0:
            version = group
            group = CORE_GROUP
        return group, version