# kubedriver

This driver implements the [Lifecycle Manager](http://servicelifecyclemanager.com/2.1.0/) Brent Resource Driver APIs to manage Kubernetes objects during lifecycle transition and operations.

# Install

The driver can be installed on [Kubernetes](install.md) using Helm.

# User Guide

The following sections explain the functionality of this driver and the requirements it places on the packages and deployment locations used for Resources.

- [Deployment Locations](user-guide/deployment-locations.md) - details the properties expected by this driver on a deployment location
- [Building a Resource](user-guide/building-a-resource.md) - files required for a resource package and how they are used
    - [Ready Checks](user-guide/ready-checks.md) - scripts used to check Kubernetes are ready as part of a transition or operation
    - [Extracting Outputs](user-guide/extracting-outputs.md) - scripts used to extract output values for a transition or operation
- [Templating](user-guide/templating.md) - details how properties of a Resource can be used as injected values in templates
- [Available Properties](user-guide/properties.md) - details the full list of properties available in templates and scripts

# Reference

- [Kegd](reference/kegd/index.md) - reference detail of the tasks available in a deployment strategy
- [Kegd Scripting](reference/kegd/scripting/index.md) - reference detail of the classes and functions available to users writing ready check and output scripts