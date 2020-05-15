from ignition.service.framework import Service, Capability
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties

class AdditionalResourceDriverProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('resource_driver')
        self.keep_files = False
        self.keep_kegdrs = False
