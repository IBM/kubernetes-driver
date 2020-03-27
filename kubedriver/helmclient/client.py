import subprocess
import tempfile
import yaml
import os
import stat
import uuid
from .exceptions import HelmError

class HelmClient:
    
    def __init__(self, kube_location):
        self.kube_location = kube_location
        self.tmp_dir = tempfile.mkdtemp()
        self.__configure_helm()
        self.helm = f'helm{self.kube_location.helm_version}'

    def __configure_helm(self):
        self.kube_conf_path = os.path.join(self.tmp_dir, 'kubeconf.yaml')
        with open(self.kube_conf_path, 'w') as f:
            yaml.dump(self.kube_location.client_config, f)
        self.helm_home_path = os.path.join(self.tmp_dir, 'helm-home')

    def __helm_cmd(self, *args):
        tmp_script = '#!/bin/sh'
        tmp_script += f'\nexport KUBECONFIG={self.kube_conf_path}'
        tmp_script += f'\nexport HELM_HOME={self.helm_home_path}'
        tmp_script += f'\n{self.helm}'
        for arg in args:
            tmp_script += f' {arg}'
        script_path = os.path.join(self.tmp_dir, f'script-{uuid.uuid4()}.sh')
        with open(script_path, 'w') as w:
            w.write(tmp_script)
        cmd = ['sh', script_path]
        return cmd

    def install(self, chart, name, namespace, values):
        cmd = self.__helm_cmd('install', chart, '--name', name, '--namespace', namespace, '-f', values)
        print(cmd)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm install failed: {process_result.stdout}')
        return name

    def get(self, name):
        cmd = self.__helm_cmd('get', name)
        if process_result.returncode != 0:
            raise HelmError(f'Helm get failed: {process_result.stdout}')

    def delete(self, name):
        cmd = self.__helm_cmd('delete', name)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm delete failed: {process_result.stdout}')

    def purge(self, name):
        cmd = self.__helm_cmd('delete', name, '--purge')
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm purge failed: {process_result.stdout}')