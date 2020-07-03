import logging
import subprocess
import tempfile
import yaml
import os
import shutil
import stat
import uuid
from .exceptions import HelmError
from .tls import HelmTls
from kubedriver.kubeobjects import ObjectConfigurationDocument
from kubedriver.helmobjects import HelmReleaseDetails

logger = logging.getLogger(__name__)

REVISION_PREFIX = 'REVISION:'
RELEASED_PREFIX = 'RELEASED:'
CHART_PREFIX = 'CHART:'
USER_SUPPLIED_VALUES_PREFIX = 'USER-SUPPLIED VALUES:'
COMPUTED_VALUES_PREFIX = 'COMPUTED VALUES:'
HOOKS_PREFIX = 'HOOKS:'
MANIFEST_PREFIX = 'MANIFEST:'

# Helm 3
NAME_PREFIX = 'NAME:'
LAST_DEPLOYED_PREFIX = 'LAST DEPLOYED:' # Replaces RELEASED_PREFIX
NAMESPACE_PREFIX = 'NAMESPACE:'
STATUS_PREFIX = 'STATUS:'



class HelmClient:
    
    def __init__(self, kube_config, helm_version, tls=None):
        self.tmp_dir = tempfile.mkdtemp()
        self.tls = tls if tls is not None else HelmTls(enabled=False)
        self.__configure_helm(kube_config)
        self.helm = f'helm{helm_version}'
        self.helm_version = helm_version

    def close(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def __configure_helm(self, kube_config):
        self.kube_conf_path = os.path.join(self.tmp_dir, 'kubeconf.yaml')
        with open(self.kube_conf_path, 'w') as f:
            yaml.dump(kube_config, f)
        self.helm_home_path = os.path.join(self.tmp_dir, 'helm-home')
        os.makedirs(self.helm_home_path)
        if self.tls.enabled == True:
            if self.tls.ca_cert != None:
                ca_cert_path = os.path.join(self.helm_home_path, 'ca.pem')
                with open(ca_cert_path, 'w') as f:
                    f.write(self.tls.ca_cert)
            if self.tls.cert != None:
                cert_path = os.path.join(self.helm_home_path, 'cert.pem')
                with open(cert_path, 'w') as f:
                    f.write(self.tls.cert)
            if self.tls.key != None:
                key_path = os.path.join(self.helm_home_path, 'key.pem')
                with open(key_path, 'w') as f:
                    f.write(self.tls.key)

    def __helm_cmd(self, *args):
        tmp_script = '#!/bin/sh'
        tmp_script += f'\nexport KUBECONFIG={self.kube_conf_path}'
        tmp_script += f'\nexport HELM_HOME={self.helm_home_path}'
        tmp_script += f'\n{self.helm}'
        for arg in args:
            tmp_script += f' {arg}'
        if self.tls.enabled is True:
            tmp_script += ' --tls'
        script_path = os.path.join(self.tmp_dir, f'script-{uuid.uuid4()}.sh')
        with open(script_path, 'w') as w:
            w.write(tmp_script)
        cmd = ['sh', script_path]
        return cmd

    def install(self, chart, name, namespace, values=None):
        if self.helm_version.startswith("3"):
            args = ['install', name, chart, '--namespace', namespace]
        else:
            args = ['install', chart, '--name', name, '--namespace', namespace]
        if values != None:
            args.append('-f')
            args.append(values)
        cmd = self.__helm_cmd(*args)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm install failed: {process_result.stdout}')
        return name

    def upgrade(self, chart, name, namespace, values=None, reuse_values=False):
        args = ['upgrade', name, chart, '--namespace', namespace]
        if values != None:
            args.append('-f')
            args.append(values)
        if reuse_values is True:
            args.append('--reuse-values')
        cmd = self.__helm_cmd(*args)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm upgrade failed: {process_result.stdout}')
        return name

    def get(self, name, namespace):
        if self.helm_version.startswith("3"):
            cmd = self.__helm_cmd('get', "all", name, '--namespace', namespace)
        else:
            cmd = self.__helm_cmd('get', name, '--namespace', namespace)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm get failed: {process_result.stdout}')
        else:
            if self.helm_version.startswith("3"):
                return self.__parse_to_helm_3_release(process_result.stdout, name, namespace)
            else:
                return self.__parse_to_helm_release(process_result.stdout, name, namespace)

    def safe_get(self, name, namespace):
        try:
            release = self.get(name, namespace)
            return True, release
        except HelmError as e:
            if f'Error: release: "{name}" not found' in str(e):
                return False, None
            raise e from None

    def delete(self, name, namespace):
        if self.helm_version.startswith("3"):
            cmd = self.__helm_cmd('delete', name, '--keep-history', '--namespace', namespace)
        else:
            cmd = self.__helm_cmd('delete', name)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm delete failed: {process_result.stdout}')

    def purge(self, name, namespace):
        if self.helm_version.startswith("3"):
            cmd = self.__helm_cmd('delete', name, '--namespace', namespace)
        else:
            cmd = self.__helm_cmd('delete', name, '--purge')
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm purge failed: {process_result.stdout}')

    def __parse_to_helm_release(self, output, name, namespace):
        output = output.decode('utf-8')
        status = HelmReleaseDetails(name=name, namespace=namespace)
        split_lines = output.splitlines()
        idx = 0
        total_lines = len(split_lines)
        while idx < total_lines:
            line = split_lines[idx]
            if line.startswith(REVISION_PREFIX) and status.revision == None:
                revision_str = line[len(REVISION_PREFIX):].strip()
                status.revision = int(revision_str)
            elif line.startswith(RELEASED_PREFIX) and status.released ==  None:
                status.released = line[len(RELEASED_PREFIX):].strip()
            elif line.startswith(CHART_PREFIX) and status.chart ==  None:
                status.chart = line[len(CHART_PREFIX):].strip()
            elif line.startswith(USER_SUPPLIED_VALUES_PREFIX) and status.user_supplied_values == None:
                captured_usv = ''
                while idx+1 < total_lines and not split_lines[idx+1].startswith(COMPUTED_VALUES_PREFIX):
                    idx += 1
                    captured_usv += f'\n{split_lines[idx]}'
                status.user_supplied_values = yaml.safe_load(captured_usv)
            elif line.startswith(COMPUTED_VALUES_PREFIX) and status.computed_values == None:
                captured_cv= ''
                while idx+1 < total_lines and not split_lines[idx+1].startswith(HOOKS_PREFIX):
                    idx += 1
                    captured_cv += f'\n{split_lines[idx]}'
                status.computed_values = yaml.safe_load(captured_cv)
            elif line.startswith(MANIFEST_PREFIX) and status.manifest == None:
                captured_manifest = ''
                while idx+1 < total_lines:
                    idx += 1
                    captured_manifest += f'\n{split_lines[idx]}'
                loaded_manifest = yaml.safe_load_all(captured_manifest)
                status.manifest = []
                for doc in loaded_manifest:
                    if doc != None: #empty doc
                        status.manifest.append(doc)
            idx += 1
        return status

    def __parse_to_helm_3_release(self, output, name, namespace):
        output = output.decode('utf-8')
        status = HelmReleaseDetails(name=name, namespace=namespace)
        split_lines = output.splitlines()
        idx = 0
        total_lines = len(split_lines)
        while idx < total_lines:
            line = split_lines[idx]
            if line.startswith(NAME_PREFIX) and status.name == None:
                status.name = line[len(NAME_PREFIX):].strip()
            elif line.startswith(LAST_DEPLOYED_PREFIX) and status.last_deployed == None:
                status.last_deployed = line[len(LAST_DEPLOYED_PREFIX):].strip()
            elif line.startswith(NAMESPACE_PREFIX) and status.namespace == None:
                status.namespace = line[len(NAMESPACE_PREFIX):].strip()
            elif line.startswith(STATUS_PREFIX) and status.status == None:
                status.status = line[len(STATUS_PREFIX):].strip()
            elif line.startswith(REVISION_PREFIX) and status.revision == None:
                revision_str = line[len(REVISION_PREFIX):].strip()
                status.revision = int(revision_str)
            elif line.startswith(USER_SUPPLIED_VALUES_PREFIX) and status.user_supplied_values == None:
                captured_usv = ''
                while idx+1 < total_lines and not split_lines[idx+1].startswith(COMPUTED_VALUES_PREFIX):
                    idx += 1
                    captured_usv += f'\n{split_lines[idx]}'
                status.user_supplied_values = yaml.safe_load(captured_usv)
            elif line.startswith(COMPUTED_VALUES_PREFIX) and status.computed_values == None:
                captured_cv= ''
                while idx+1 < total_lines and not split_lines[idx+1].startswith(HOOKS_PREFIX):
                    idx += 1
                    captured_cv += f'\n{split_lines[idx]}'
                status.computed_values = yaml.safe_load(captured_cv)
            elif line.startswith(MANIFEST_PREFIX) and status.manifest == None:
                captured_manifest = ''
                while idx+1 < total_lines:
                    idx += 1
                    captured_manifest += f'\n{split_lines[idx]}'
                loaded_manifest = yaml.safe_load_all(captured_manifest)
                status.manifest = []
                for doc in loaded_manifest:
                    if doc != None: #empty doc
                        status.manifest.append(doc)
            idx += 1
        return status