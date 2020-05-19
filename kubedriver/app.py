import logging
import ignition.boot.api as ignition
import pathlib
import os
import kubedriver.config as driverconfig
from ignition.service.queue import JobQueueCapability
from ignition.service.templating import TemplatingCapability, ResourceTemplateContextCapability 
from kubedriver.resourcedriver import (KubeResourceDriverHandler, AdditionalResourceDriverProperties, ExtendedResourceTemplateContext,
                                        NameManager)
from kubedriver.kubeclient import KubeApiControllerFactory
from kubedriver.keg import KegPersistenceFactory
from kubedriver.kegd import KegdStrategyProcessor, KegdStrategyManager, KegDeploymentProperties, KegDeploymentStrategyProperties, KegdReportPersistenceFactory
from kubedriver.kegd.model import DeploymentStrategyFileReader, DeploymentStrategyParser
from kubedriver.locationcontext import LocationContextFactory

default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')

def create_app():
    app_builder = ignition.build_resource_driver('kubedriver')
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./kubedriver_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/kubedriver/kubedriver_config.yml', required=False)
    app_builder.include_environment_config_properties('KUBEDRIVER_CONFIG', required=False)

    app_builder.add_property_group(AdditionalResourceDriverProperties())
    app_builder.add_property_group(KegDeploymentProperties())

    app_builder.add_service(NameManager)
    app_builder.add_service(KegPersistenceFactory)
    app_builder.add_service(KegdReportPersistenceFactory)
    app_builder.add_service(KubeApiControllerFactory)
    app_builder.add_service(LocationContextFactory, 
            api_ctl_factory=KubeApiControllerFactory,
            kegd_persister_factory=KegdReportPersistenceFactory, 
            keg_persister_factory=KegPersistenceFactory
    )
    app_builder.add_service(ExtendedResourceTemplateContext, 
            name_manager=NameManager
    )
    app_builder.add_service(DeploymentStrategyParser)
    app_builder.add_service(DeploymentStrategyFileReader, 
            deployment_strategy_properties=KegDeploymentStrategyProperties, 
            templating=TemplatingCapability, 
            parser=DeploymentStrategyParser
    )
    app_builder.add_service(KegdStrategyProcessor, 
            context_factory=LocationContextFactory, 
            templating=TemplatingCapability, 
            job_queue=JobQueueCapability
    )
    app_builder.add_service(KegdStrategyManager, 
            context_factory=LocationContextFactory, 
            templating=TemplatingCapability, 
            job_queue=JobQueueCapability,
            kegd_properties=KegDeploymentProperties
    )
    app_builder.add_service(KubeResourceDriverHandler, 
            resource_driver_properties=AdditionalResourceDriverProperties, 
            kegd_strategy_manager=KegdStrategyManager,
            kegd_file_reader=DeploymentStrategyFileReader, 
            render_context_service=ResourceTemplateContextCapability, 
            name_manager=NameManager
    )

    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()