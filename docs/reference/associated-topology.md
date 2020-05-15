# Associated Topology

This section covers the entires included on the `associateTopology` field on lifecycle execution responses from this driver. These entries are picked up by Brent to build a view of the "internalResources" of the Resource.

**Table of Contents**
- [Topology Types](#topology-types)
  - [Objects](#objects)
    - [Deployed Object](#deployed-object)
    - [Removed Object](#removed-object)
    - [Updated Object](#updated-object)
  - [Helm Releases](#helm-releases)
    - [Deployed Helm Release](#deployed-helm-releases)
    - [Removed Helm Release](#removed-helm-releases)
    - [Updated Helm Release](#updated-helm-releases)
- [Examples](#examples)

# Topology Types

## Objects

### Deployed Object

A topology entry for an object deployed by this driver will be in the format:

```
associatedTopology:
  <group>:<kind>:<metadata.namespace>:<metadata.name>:
    id: <metadata.uid>
    type: <group>:<kind>
```

As an example, for a ConfigMap named `example` in the `docs` namespace:

```
associatedTopology:
  v1:ConfigMap:docs:example:
    id: a6b5e9e1-9688-11ea-98ae-005056956986
    type: v1:ConfigMap
```

This means the internal resource entry in Brent will be:

```
name: v1:ConfigMap:docs:example
id: a6b5e9e1-9688-11ea-98ae-005056956986
type: v1:ConfigMap
```

The reasoning behind this is any object of a particular type (group/apiVersion and kind) is unique by it's name in a namespace (if the object is namespaced). For example, you can have a all of the following objects named `example`:

- v1:ConfigMap named example in the `first` namespace
- v1:ConfigMap named example in the `second` namespace
- v1:Service named example in the `first` namespace

Therefore, all of group, kind, name and namespace is needed for the associated topology key, so it does not override other objects with the same name but in different namespaces or of different types. 

For the type attribute, `<group>:<kind>` is used as this should be enough to identify the objects of the same type.

### Removed Object

If an object is removed then an entry will be included with a `null` value. As an example, when a ConfigMap named `example` in the `docs` namespace is removed the entry will be:

```
v1:ConfigMap:docs:example: null
```

### Updated Object

Updated objects are never shown in the associated topology. If they are updated in a way that moves them to a new namespace or with a new name they will appear as a "removed object" entry (with the old name) and a "deployed object" with the new one.

## Helm Releases

### Deployed Helm Release

A topology entry for a Helm release deployed by this driver will be in the format:

```
Helm:<namespace>:<name>:
  id: <namespace>:<name>
  type: Helm
```

As an example, for a Helm release named `example` in the `docs` namespace:

```
associatedTopology:
  Helm:docs:example:
    id: docs:example
    type: Helm
```

This means the internal resource entry in Brent will be:

```
name: Helm:docs:example
id: Helm:docs:example
type: Helm
```

The driver uses the name of the Helm release and the namespace it was installed in as a unique id and name (even though we are using Helm2, this prepares us for Helm3 where releases can have the same name but in different namespaces). 

The driver will also include a [Deployed Object](#deployed-object) entry for each object deployed as part of the Helm chart.

### Removed Helm Release

If a Helm release is removed then an entry will be included with a `null` value. As an example, when a Helm release named `example` in the `docs` namespace is removed the entry will be:

```
Helm:docs:example: null
```

The driver will also include a [Removed Object](#removed-object) entry for each object removed by the removal of the Helm release.

### Updated Helm Release

When a Helm release is updated (so a helm upgrade) it may lead to new objects being deployed and the removal of some existing objects. When this occurs, the driver will include a [Deployed Object](#deployed-object) entry for any new object deployed as part of the upgrade, then a [Removed Object](#removed-object) entry for any object removed as part of the upgrade. 

The Helm release will not appear in the response as it has not been deployed or removed. 

# Examples

All examples use the `doc` namespace. 

Example with deployed object named `example`:
```
associatedTopology:
  v1:ConfigMap:doc:example:
    id: 465d076c-96be-11ea-98ae-005056956986
    type: v1:ConfigMap
```

Example with removed object named `example`:
```
associatedTopology:
  v1:ConfigMap:doc:example: null
```

Example with deployed Helm release named `example`:
```
associatedTopology:
  Helm:doc:example:
    id: Helm:doc:example
    type: Helm
  apps/v1:Deployment:doc:example-nginx-ingress-controlle:
    id: dff72633-96c0-11ea-98ae-005056956986
    type: apps/v1:Deployment
  apps/v1:Deployment:doc:example-nginx-ingress-default-b:
    id: dff8d818-96c0-11ea-98ae-005056956986
    type: apps/v1:Deployment
  rbac.authorization.k8s.io/v1beta1:ClusterRole:a3fa7d7c8-54b2-4d7d-8324-7752b64e7296-4-nginx-ingress:
    id: dfd67625-96c0-11ea-98ae-005056956986
    type: rbac.authorization.k8s.io/v1beta1:ClusterRole
  rbac.authorization.k8s.io/v1beta1:ClusterRoleBinding:a3fa7d7c8-54b2-4d7d-8324-7752b64e7296-4-nginx-ingress:
    id: dfd82cb2-96c0-11ea-98ae-005056956986
    type: rbac.authorization.k8s.io/v1beta1:ClusterRoleBinding
  rbac.authorization.k8s.io/v1beta1:Role:doc:example-nginx-ingress:
    id: dfde6ee3-96c0-11ea-98ae-005056956986
    type: rbac.authorization.k8s.io/v1beta1:Role
  rbac.authorization.k8s.io/v1beta1:RoleBinding:doc:example-nginx-ingress:
    id: dfe0b5a7-96c0-11ea-98ae-005056956986
    type: rbac.authorization.k8s.io/v1beta1:RoleBinding
  v1:Service:doc:example-nginx-ingress-controlle:
    id: dfefa9fb-96c0-11ea-98ae-005056956986
    type: v1:Service
  v1:Service:doc:example-nginx-ingress-default-b:
    id: dff52f4c-96c0-11ea-98ae-005056956986
    type: v1:Service
  v1:ServiceAccount:doc:example-nginx-ingress:
    id: dfb4f7b8-96c0-11ea-98ae-005056956986
    type: v1:ServiceAccount
  v1:ServiceAccount:doc:example-nginx-ingress-backend:
    id: dfb77967-96c0-11ea-98ae-005056956986
    type: v1:ServiceAccount
``` 

Example with removed Helm release named `example`:
```
associatedTopology:
  Helm:doc:example: null
  apps/v1:Deployment:doc:example-nginx-ingress-controlle: null
  apps/v1:Deployment:doc:example-nginx-ingress-default-b: null
  rbac.authorization.k8s.io/v1beta1:ClusterRole:a3fa7d7c8-54b2-4d7d-8324-7752b64e7296-4-nginx-ingress: null
  rbac.authorization.k8s.io/v1beta1:ClusterRoleBinding:a3fa7d7c8-54b2-4d7d-8324-7752b64e7296-4-nginx-ingress: null
  rbac.authorization.k8s.io/v1beta1:Role:doc:example-nginx-ingress: null
  rbac.authorization.k8s.io/v1beta1:RoleBinding:doc:example-nginx-ingress: null
  v1:Service:doc:example-nginx-ingress-controlle: null
  v1:Service:doc:example-nginx-ingress-default-b: null
  v1:ServiceAccount:doc:example-nginx-ingress: null
  v1:ServiceAccount:doc:example-nginx-ingress-backend: null
```