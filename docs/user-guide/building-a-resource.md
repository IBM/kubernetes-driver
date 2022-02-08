# Building a Resource

This section assumes you already have an understanding of how to build a package for a Resource managed by Brent (the Resource Manager included with ALM). If you do not, see the [official documentation](http://servicelifecyclemanager.com/2.1.0/user-guides/resource-engineering/resource-packages/brent/create-brent-resource-package/) on this subject. 

**Table of Contents**:

- [Kubernetes Driver Files](#kubernetes-driver-files)
  - [Objects](#objects)
  - [Helm Charts](#helm-charts)
- [Kubernetes Entity Group Deployment](#kubernetes-entity-group-deployment) (kegd.yaml)
  - [Deploying Objects](#deploying-objects)
  - [Removing Objects](#removing-objects)
    - [Created on Create/Install/Start](#created-on-create/install/start)
    - [Created on Other Transitions](#created-on-other-transitions)
    - [Matching Operation Calls](#matching-operation-transitions)
    - [Remove Immediately](#remove-immediately)
  - [Updating Objects](#updating-objects)
  - [Deploying Helm Charts](#deploying-helm-charts)
  - [Updating Helm Releases](#updating-helm-releases)
  - [Removing Helm Releases](#deploying-helm-releases)
  
# Kubernetes Driver Files

Once you have the skeleton for a Brent Resource, you can begin adding the files required to use this Kubernetes driver to implement any of the lifecycle transition or operations. 

Initially you will need to create a `kubernetes` directory in the `Lifecycle` directory of your Resource:

```
Definitions/
  lm/
    resource.yaml
Lifecycle/
  kubernetes/
    helm/
      *.tgz
      *.yaml
    objects/
      *.yaml
    kegd.yaml
```

The following files and directories should be included in `kubernetes`:

| Name | Type | Description | 
| --- | --- | --- |
| kegd.yaml (kegd.yml, keg.yaml and keg.yml are also allowed) | YAML File | Describes the strategy for deploying objects/helm charts on each transition or operation of the Resource, see more on this file later | 
| objects | Directory | Directory of Kubernetes object configuration files (Deployments, Services etc.) to be deployed at various stages of the Resource lifecycle| 
| helm | Directory | Directory of Helm charts and values files to be deployed at various stages of the Resource lifecycle | 

## Objects

The Kubernetes driver can deploy any object managed by your target Kubernetes environments e.g. Deployments, Services, Config Maps... (Kubernetes documentation sometimes refer to these as "Resources" but we won't use that term in this documentation to avoid confusion with the ALM Resource)

The `objects` directory should include YAML files in the [Kubernetes object configuration file format](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/) for all objects that may be deployed as part of any transition or operation on your Resource. 

Each object configuration file may include multiple objects separated by the YAML document separator (by doing so the objects cannot be deployed on seperate transitions/operations, so only group them this way if it makes sense for your Resource). 

Example Object Configuration:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-a
data:
  dataA: valueA
  dataB: valueB
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-b
data:
  dataA: valueA
  dataB: valueB
  dataC: valueC
```

The file may include any object type understood by your target Kubernetes cluster, including [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) managed by the operator pattern.

A simpe rule of thumb: if you can create it with `kubectl apply` then you should be able to create it with this driver.

### Templating Object Configuration

The object configuration file may make use of [Jinja2 template variables syntax](https://jinja.palletsprojects.com/en/2.10.x/templates/#variables) to inject property values from the Resource descriptor:

Example template syntax to inject value of property "dataA":
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-a
data:
  dataA: {{ dataA }}
  dataB: valueB
```

The template is rendered as text before it is parsed as YAML, so there is no need to wrap the template syntax in quotes when it's the first item on a line.

For full details on templates and the syntax used, check out the [Templating](templating.md) section of this user guide.

## Helm Charts

The Kubernetes driver can deploy any helm charts to your target Kubernetes environments as long as Helm has been initialised on the environment.

The Helm charts must be compatible with Helm 3 (helm v.3.8.0 is included in the driver).

The `helm` directory should include the packaged Helm charts you intend to install (`.tgz` files) and any values files you may use to configure the installation. We'll see how you install the charts and select your values file later.

Example package:
```
Lifecycle/
  kubernetes/
    helm/
      mychart-1.0.0.tgz
      custom-values.yaml
    kegd.yaml
```

Where `custom-values.yaml` includes:

```
# Example properties, the contents here depends on the values supported by your helm chart
service:
  nodePort: 32445
```

The template is rendered as text before it is sent to the Helm command, so there is no need to wrap the template syntax in quotes when it's the first item on a line.

For full details on templates and the syntax used, check out the [Templating](templating.md) section of this user guide.

### Templating Values Files

The values files may make use of [Jinja2 template variables syntax](https://jinja.palletsprojects.com/en/2.10.x/templates/#variables) to inject property values from the Resource descriptor:

```
# Example properties, the contents here depends on the values supported by your helm chart
service:
  nodePort: {{ servicePort }}
```

# Kubernetes Entity Group Deployment

The Kubernetes driver can deploy any number of Kubernetes objects as part of a Resource, at different stages of it's lifecycle. The driver keeps track of the objects it has deployed for a single Resource in a Kubernetes Entity Group, known as a Keg. 

This includes objects created through the installation of Helm charts, which we will come to later. Even if you only intend to use Helm charts, we recommend reading the rest of the section on objects as the general process for deploying and removing them is the same.

You are in control of when objects are deployed into and removed from the Keg through a deployment strategy (kegd = keg deployment). 

This strategy is written in a YAML formatted file and should be included in top level of the Kubernetes directory in your Resource package. 

```
Definitions/
  lm/
    resource.yaml
Lifecycle/
  kubernetes/
    kegd.yaml
```

It should include a list of compose tasks which dictate the objects to deploy for each transition or operation called on this driver for your Resource. 

## Deploying Objects

One compose task you may use is the `objects` task, which signals the deployment of objects from a file contained in the objects directory of your Resource package. 

For example, on a Create transition you can request the deployment of the objects in the `my-deployment.yaml` and `my-Service.yaml` files (these files should exist in the `objects` directory of the Resource package kubernetes directory). 

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml
```

The objects are created in the order they are listed (and the order they appear in the file if there are multiple objects). Also, the files are rendered as templates, as described in [Templating Object Configuration](#templating-object-configuration), before they are applied, allowing you to inject the values of Resource and/or system properties to the object spec. 

You may also use a template value for the `file` argument, to choose a file based on Resource and/or system properties. The example shown below selects a file based on the `file_to_use` property (which should be included on the Resource descriptor):

```
compose:
  - name: Create
    deploy:
      - objects:
          file: "{{ file_to_use }}"
```

If any of the object’s are of a Kind that is namespaced, they are deployed into the namespace declared in the metadata section of the object’s configuration. If a namespace has not been included then the default from the deployment location properties is used. 

To add tasks for another transition or operation, add a new entry to the compose list and fill it with tasks. For example, you could deploy objects in a my-job.yaml on an operation called ExecuteMyJob: 

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml

  - name: ExecuteMyJob 
    deploy:
      - objects:
          file: my-job.yaml
```

## Removing Objects 

### Created on Create/Install/Start 

Eventually you will need to the remove objects deployed as part of a Resource. By default, the Kubernetes driver will automatically remove objects on the reverse transition they were created in, without any extra configuration required by the user. 

For example, in our earlier case, you created some objects on Create: 

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml
```

In this case the driver will assume these objects should be removed on the Delete transition. Similarly, objects deployed on Install are removed on Uninstall and objects deployed on Start are removed on Stop. 

### Created on Other Transitions 

All other objects, created on Configure or custom operations, will be deleted when the group is deleted, which by default is on the Delete transition of the Resource. 

However, if you don’t intend to use the Delete transition on your Resource (or it is handled by a different driver) then you must set the `cleanupOn` value in your deployment strategy. 

```
cleanupOn: Uninstall
compose:
  - name: Install
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml
``` 

The above example will cause all objects to be removed on the Uninstall transition. This will make sure all our objects are removed, eventually, on the last transition of the Resource. 

**Note:** it’s important to note that if you don’t include the correct lifecycle transitions in your Resource descriptor, or don’t configure them to use the Kubernetes driver, then you may end up with dangling objects left in your cluster. For example, if you change the global “cleanupOn” value to Uninstall but then don’t include the Uninstall transition on your Resource, some objects may never be removed. 

The global cleanupOn value is a catch all, ensuring any objects we’ve created so far are removed, regardless of when they were deployed. This should keep the cluster clean when the owning Resource has been removed.

It’s also reasonable to want to remove objects created by Configure or a custom operation much earlier in the Resource lifecycle. To handle these cases (or to change the default for objects deployed in Create/Install/Start), you may set the “cleanupOn” value for a specific compose entry:

```
compose:
  - name: AddToList
    cleanupOn: RemoveFromList
    deploy:
      - objects:
          file: add.yaml
``` 

In the above example we want to deploy an object in the “add.yaml” file as part of an AddToList operation, to configure a new entry to a load balancer. We then remove the entry on a RemoveFromList operation. 

### Matching Operation Calls 

The above example showed you how to link operations with their reverse call but what if we call AddToList 5 times and on each occasion a unique object is created, then call RemoveFromList? Bad news, the first call to RemoveFromList will remove all 5 instances. The good news is you can configure this behaviour with the “uniqueBy” setting for a compose entry. 

This setting must include a list of the properties whose values make each execution of this operation unique.

For example, in our AddToList operation, we expect a value on a property called “targetIp” which identifies the IP to add to our load balancer. This means on a RemoveFromList call, we expect the same value for this property to indicate the IP to remove. This makes “targetIp” the unique property of this execution and should be used as the value of “uniqueBy”: 

```
compose:
  - name: AddToList
    cleanupOn: RemoveFromList
    deploy:
      - objects:
          file: add.yaml
    uniqueBy:
      - targetIp
``` 

Now when RemoveFromList is called the driver will only remove the object(s) created when AddToList was called with the same value of the “targetIp” property.

If the call is unique by additional properties, we include them as items in the list:

```
compose:
  - name: AddToList
    cleanupOn: RemoveFromList
    deploy:
      - objects:
          file: add.yaml
    uniqueBy:
      - targetIp
      - hostName
``` 

In the above example, each call is unique by a combination of both "targetIp" and "hostName".

### Remove immediately 

It may also be the case that you intend to deploy an object for a transition/operation but have no use for it after completion. 

For example, on a Configure we may want to run a job to its completion then remove it to keep our cluster tidy. To do this, we need an understanding of readiness checks, which will come later in this guide, but just know we are able to wait for the job completes before considering the transition a success. 

To request the job is immediately removed at the end of the transition execution (after we’ve confirmed the job completed) we can add an `immediateCleanupOn` setting to the objects task: 

```
compose:
  - name: Configure
    deploy:
      - objects:
          file: some-objects.yaml
        immediateCleanupOn: Success
```

Possible values for this setting include: 
- Never - the default behaviour, to keep the object until the cleanupOn settings dictate it should be removed 
- Success - the object should be removed after the transition/operation completes successfully 
- Failure - the object should be removed only if the transition/operation fails
- Always - always remove the object at the end of the transition/operation 

## Updating Objects 

Any object deployed as part of a transition/operation is expected to be unique and to not exist in the target cluster. 

However, to remain idempotent, if the driver finds an object already exists and was deployed as part of the same Resource it will be updated.

There is a side effect to this. The object will now be cleaned up on either the first transition’s cleanup rules or the second’s. 

For example, if you deploy the same object on both Create and Start (so it is updated on Start), the object is set to be cleaned up on both Stop and Delete (so will usually be removed on Stop as this is called before Delete). This is ok, as the Delete call will not fail if the object has been removed previously, however this may not be your desired behaviour. 

## Deploy Helm Charts 

The driver also supports installing (and deleting) Helm charts. To install a chart during a lifecycle transition/operation add the `helm` task to the compose entry: 

```
compose:
  - name: Create
    deploy:
      - helm:
          chart: my-chart-1.0.0.tgz
          name: my-release-name
```

The value of `chart` must be either a file in the `helm` directory of your Resource’s Kubernetes directory or the name of a chart from a repository (that has been configured on the Helm server of your deployment location) e.g. `stable/nginx-ingress`. 

A value must be set to give the release a name and you may optionally set the namespace to use (otherwise the default on the deployment location is used). 

You may also include the `values` option with the name of a file (also found in the helm directory) to customise the installation values. This file will be rendered as a template so you may inject Resource and/or system properties before it is used.

You may also include the `wait` and `timeout` options in order to leverage the Helm wait functionality. See [helm reference](/docs/reference/kegd/helm.md#wait) for more information.

In addition, the values of chart, name, namespace and values are also rendered as templated strings, so you may inject Resource and/or system properties:

```
compose:
  - name: Create
    deploy:
      - helm:
          chart: my-chart-1.0.0.tgz
          name: r{{ system_properties.resource_id_label }}
```

**Note:** care should be taken with the value of `name` as a Helm release name cannot exceed 53 characters and must start with an alphabetic letter. 

## Updating Helm Releases

To remain idempotent, if the driver finds the helm release already exists and was deployed as part of the same resource it will be upgraded.

There is a side effect to this. The helm release will now be cleaned up on either the first transition’s cleanup rules or the second’s. 

For example, if you deploy the same helm release on Create and Start (so it has been re-deployed on Start), the release is set to be cleaned up on both Stop and Delete so will usually be removed on Stop as this is called before Delete. This is ok, as the Delete call will not fail if the helm release has been removed previously, however this may not be your desired behaviour.

## Removing Helm Releases

The removal of installed Helm charts follows the same rules as objects: 

- They may be removed at the end of the transition/operation by specifying an `immediateCleanupOn` value
- Otherwise they are removed on the transition/operation’s `cleanupOn` setting  (considering the value of `uniqueBy` if provided) 
- Otherwise they are removed when the Keg is deleted, based on the global `cleanupOn` value 

# Next Steps

See how to add [ready checks](ready-checks.md) in order to inspect objects statuses before completing a transition/operation.

Also, check out [extracting-outputs](extracting-outputs.md) in order to return fields from an object's status as outputs on the transition/operation (for Brent to set these properties on the Resource).

A complete guide to the tasks and arguments used in the `kegd.yaml` file can be found at [here](../reference/kegd/index.md)
