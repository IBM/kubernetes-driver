# Best Practices

This document outlines some best practices to follow when building Resources which make use of the Kubernetes driver

## Use resource_subdomain or a property for object names

Objects of the same type must have unique names (in the same namespace, if they are namespace scoped), so care should be taken when giving objects names as part of your Resource.

If you hard code the name, then only one instance of this Resource can exist:

_Object Configuration_
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
```

Consider using the `resource_subdomain` or `resource_label` properties, as they are Kubernetes safe object names based on the Resource's name and ID, so they are guaranteed to be unique:

_Object Configuration_
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ system_properties.resource_subdomain }}
```

Alternatively, add a property to your descriptor to supply the name for each instance (`name` is a reserved word in ALM):

_Resource Descriptor_
```
properties:
  deployment-name: 
    type: string
```

_Object Configuration_
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ deployment-name }}
```

## No properties called namespace

It would appear sensible to use `namespace` as the name of a property which dictates the installation namespace of an object - but don't. Example:

_Resource Descriptor_
```yaml
properties:
  namespace: 
    type: string
```

_Object Configuration_
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ controllerName }}
  namespace: {{ namespace }}
```

This will fail, as `namespace` is a reserved word in the templating language used. 

