import logging
import ignition.boot.api as ignition
import pathlib
import os
import kubedriver.config as driverconfig
from ignition.service.queue import JobQueueCapability
from kubedriver.infrastructure import InfrastructureDriver
from kubedriver.kubeclient import KubeClientDirector
from kubedriver.kubegroup import EntityGroupManager, ManagerContextLoader
from kubedriver.location import KubeDeploymentLocationTranslator

default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')

def create_app():
    app_builder = ignition.build_driver('kubedriver', vim=True)
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./kubedriver_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/kubedriver/kubedriver_config.yml', required=False)
    app_builder.include_environment_config_properties('KUBEDRIVER_CONFIG', required=False)
    app_builder.add_service(KubeDeploymentLocationTranslator)
    app_builder.add_service(ManagerContextLoader, KubeClientDirector())
    app_builder.add_service(EntityGroupManager, context_loader=ManagerContextLoader, job_queue=JobQueueCapability)
    app_builder.add_service(InfrastructureDriver, deployment_location_translator=KubeDeploymentLocationTranslator, keg_manager=EntityGroupManager)
    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()