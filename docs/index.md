# kubedriver

This driver implements the [Lifecycle Manager](http://servicelifecyclemanager.com/2.1.0/) Brent Infrastructure APIs to manage Kubernetes objects as infrastructure.

# Install

The driver can be installed on [Kubernetes](./k8s-install.md) using Helm.

# User Guide

The following sections explain the functionality of this driver and the requirements it places on the infrastructure templates and deployment locations used for Resources.

- [Infrastructure Templates](./user-guide/infrastructure-templates.md) - supported templates and types for infrastructure
- [Property Handling](./user-guide/property-handling.md) - details how properties for a Resource are handled during requests
- [Deployment Locations](./user-guide/deployment-locations.md) - details the properties expected by this driver on a deployment location
