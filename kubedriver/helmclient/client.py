import subprocess
import tempfile
import yaml
import os
import shutil
import stat
import uuid
from .exceptions import HelmError

class HelmClient:
    
    def __init__(self, kube_config, helm_version):
        self.tmp_dir = tempfile.mkdtemp()
        self.__configure_helm(kube_config)
        self.helm = f'helm{helm_version}'

    def close(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def __configure_helm(self, kube_config):
        self.kube_conf_path = os.path.join(self.tmp_dir, 'kubeconf.yaml')
        with open(self.kube_conf_path, 'w') as f:
            yaml.dump(kube_config, f)
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

    def install(self, chart, name, namespace, values=None):
        args = ['install', chart, '--name', name, '--namespace', namespace]
        if values != None:
            args.append('-f')
            args.append(values)
        cmd = self.__helm_cmd(*args)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process_result.returncode != 0:
            raise HelmError(f'Helm install failed: {process_result.stdout}')
        return name

    def get(self, name):
        cmd = self.__helm_cmd('get', name)
        process_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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