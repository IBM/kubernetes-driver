# Extracting Outputs 

If you've made it here then you should have already read [Building a Resource](building-a-resource.md) and have an idea of how to setup a resource package and draft a deployment strategy (the kegd.yaml file).

It's good to also have an understanding of [Ready Checks](ready-checks.md) as this is executed before any outputs can be extracted.

Outputs are property values you would like to return on any lifecycle transition/operation request. These values are consumed by Brent and stored on the resource. Subsequent transition/operation requests can then reference these values as properties in templates and/or scripts. If the property exists on the resource descriptor, then the value will be visible in the ALM topology and can be mapped to other resources in an Assembly design (note: only outputs set on Create or Install transitions will be consumed by the ALM topology).

Usually, you will want to retrieve a value from an object to use as an output value and, in most cases, this field will come from the `status` field of the object. In [Ready Checks](ready-checks.md) we discussed how every object in Kubernetes has a different definition for it's `status` (and `spec` too but those are usually inputs). 

As a result, the driver provides hooks for the resource developer to plug-in scripts (with Python syntax) which may navigate the status of the objects deployed as part of the resource to extract outputs. This script is only executed after the ready check has passed (when no ready check exists the outputs are extracted immediately after the objects have been deployed).

Unlike the scripts used for ready checks, the output extraction script is only executed once for a transition/operation.

Each transition/operation may share or use different scripts or provide no script at all, in which case no outputs are extracted.

# Add an output extraction script

To add an output extraction script to your resource, you will need to create a `scripts` directory in the `kubernetes` directory of your resource:

```
Definitions/
  lm/
    resource.yaml
Lifecycle/
  kubernetes/
    objects/
      *.yaml
    scripts/
      *.py
    kegd.yaml
```

Add a new Python file (.py extension) to the scripts directory, with any name of your choosing:

```
Lifecycle/
  kubernetes/
    objects/
      *.yaml
    scripts/
      outputs-on-create.py
    kegd.yaml
```

We'll talk about the contents of this file later. For now, we'll configure our Create transition to use this script by modifying the `kegd.yaml` file. Add a `getOutputs` field to the compose entry for Create and specify the name of your script.

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml
    checkReady:
      script: check-ready-on-create.py
    getOutputs: outputs-on-create.py
```

Now, on a Create transition for this resource, the driver will deploy the objects, execute the `check-ready-on-create.py` script until it returns a "ready" result, then execute the `outputs-on-create.py` to extract outputs.

# Writing a ready check script

Output extraction scripts are written in Python syntax but it's worth noting that you will not have the full power of the language at your disposal. For example, you won't be able to import modules and perform API calls out to external systems.

Instead, you will provide a `getOutputs` function like so:

```
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    # Do the work here
    pass 
```

This function is the one called by the driver to perform the output extraction. The arguments to this function are as follows:

| Name | Description |
| --- | --- |
| keg | A collection of all the objects/helm releases deployed as part of this resource (only those that still exist, so any objects that have been removed by a transition are not included) |
| props | A dictionary of all the properties available for this resource. These are the same properties used when rendering templates |
| resultBuilder | Helper object for managing the result | 
| log | Utility to log messages to (see more later) |
| *args and **kwargs | Python constructs for consuming any additional arguments passed to this function. You won't need to use them, so they are not required but it is highly recommended, as it will keep your scripts compatible with later versions of the driver if new arguments are added to this interface |

## Keg

The keg value can be used to retrieve members deployed as part of this resource. This includes any objects/helm releases deployed in earlier transitions/operations and the current one. Any members removed in earlier transitions/operations or the current one are not included.

**Note:** objects/helm releases marked with `immediateCleanupOn` are still available in the `keg` during the output extraction and are only removed afterwards.

### Objects

Each object deployed directly (so without Helm) is retrievable by it's apiVersion (sometimes referred to as group), kind, name and namespace (if not a cluster wide type). For example, if in our `my-deployment.yaml` file we have deployed the following:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: Example
  namespace: demo
spec:
    ...spec data...
```

We can retrieve this object like so:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', 'Example', namespace='demo')

    #Alternative if you prefer snake case:
    #found, deployment = keg.get_object('apps/v1', 'Deployment', 'Example', namespace='demo')
```

**Note:** this does not perform an API call on Kubernetes, the driver has already pre-fetched all the possible objects

The variable names `found` and `deployment` can be any valid Python variable name of your choosing. 

The value of `found` is a boolean (True/False) to indicate if the object is in the keg. When `False`, the value of `deployment` will instead be `None`. You should always check `found` before proceeding to use the value of `deployment`. 

When `found` is `True`, the value of `deployment` will be a dictionary copy of the object's configuration and status, for example:

```python
{
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': 'Example',
        'namespace': 'demo'
    },
    'spec': {
        ...the spec...
    },
    'status': {
        ...the status...
    }
}
```

You can use this to inspect the contents of the object:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', 'Example', namespace='demo')
    if found:
        # deploymentName will equal 'Example'
        deploymentName = deployment['metadata']['name']
```

### Helm Releases

Each Helm release deployed is retrievable by it's name and namespace (Releases are actually unique by their name in Helm2 but in future Helm versions they will be unique by namespace as well, so best to use both to avoid compatiblity issues).

As an example, if we've deployed a Helm chart in our kegd.yaml file:

```yaml
compose:
  - name: Create
    deploy:
      - helm:
          chart: nginx-ingress-1.24.4.tgz
          name: MyReleaseName
          namespace: MyNamespace
```

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, helm_release = keg.helm_releases.get('MyReleaseName', 'MyNamespace')
```

The variable names `found` and `helm_release` can be any valid Python variable name of your choosing. 

The value of `found` is a boolean (True/False) to indicate if the helm release is in the keg. When `False`, the value of `helm_release` will be `None`. You should always check `found` before proceeding to use the value of `helm_release`. 

When `found` is `True`, the value of `helm_release` will be a special Helm object with two attributes: 

`info` - dictionary of details related to the Helm release
`objects` - a collection of the objects managed by this Helm release

Example of `info`:

```python
{
  'name': 'MyReleaseName',
  'namespace': 'MyNamespace',
  'revision': 1,
  'released': 'Mon Mar 30 13:04:31 2020',
  'chart': 'nginx-ingress-1.24.4',
  ...
}
```

The `objects` attribute has the same functions as `keg.objects`, so you can lookup objects in the Helm release by their apiVersion, kind, name and namespace.

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, helm_release = keg.helm_releases.get('MyReleaseName', 'MyNamespace')
    if found:
      objFound, controller = helm_release.objects.get('v1', 'Service', 'MyReleaseName-nginx-ingress-controller', namespace=helm_release.info['namespace'])
```

## Props

A dictionary of all the properties available for this resource. These are included as they are the same properties used when rendering templates, so if you've used them to configure identifying elements of an object, you will need them again to find it.

For example, if in our `my-deployment.yaml` file we have deployed the following:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ system_properties.resource_subdomain }}
  namespace: demo
spec:
    ...spec data...
```

Then you will need to use the same value to retrieve the object:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', props['system_properties']['resource_subdomain'], namespace='demo')
```

You may also return the properties as outputs. Normally this would seem odd as the properties were originally inputs to this request however it may be useful to return a generated `system_property` such as `resource_subdomain`, which may have been used as an identifier for an object. (See how to return this as an output later).

Check out the full range of [available properties](properties.md) later in the user guide.

## Result Builder

The `resultBuilder` allows you to set output values. By default, the `resultBuilder` is empty.

To set the value of an output, use the `setOutput` (or `set_output`) function on the builder. If the output has been prevously set, it will be overwritten. 

```python
resultBuilder.setOutput('propertyName', 'propertyValue')
```

Any value passed to `setOutput` will be converted to a string (using the `str()` method).

To return a field from an object, first retrieve the object and then set the output:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, service = keg.objects.get('v1', 'Service', props['system_properties']['resource_subdomain'], namespace='demo')
    if found:
        resultBuilder.setOutput('nodePort', service['spec']['nodePort'])
```

To return a generated `system_property` as an output, retrieve the value from `props` and pass it to `setOutput`:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    resultBuilder.setOutput('uniqueName', props['system_properties']['resource_subdomain'])
```

In addition to returning outputs, the resultBuilder can be used to exit with an error if something is not right, using `failed`:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, service = keg.objects.get('v1', 'Service', props['system_properties']['resource_subdomain'], namespace='demo')
    if not found:
        return resultBuilder.failed(f'Could not find service "{props['system_properties']['resource_subdomain']}"')
```

When a failure is returned, the driver marks the transition/operation as failed and does not return any outputs.

**What is this `f'Could not find Deployment...'` syntax?**: Python syntax to format a string with variables. Start a string with `f'` then reference a variable or function in the string to have it's value injected at runtime

## Log

Allows you to return string messages back to the driver, which may included in any log or error messages produced by the driver related to this script. There is no requirement to use the `log` but it might be useful for debugging unexpected errors during execution. 

To add a new message to the log, use the `entry` function:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    log.entry('Log something useful')
```

The log is limited to 100 entries, any message added after reaching this limit will lead to the earliest message being removed.

## Complete example

Below is an academic example of using all of the arguments together to produce a output extraction script:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, service = keg.objects.get('v1', 'Service', props['system_properties']['resource_subdomain'], namespace='demo')
    if not found:
        return resultBuilder.failed(f'Could not find service "{props['system_properties']['resource_subdomain']}"')
    resultBuilder.setOutput('nodePort', service['spec']['nodePort'])
    resultBuilder.setOutput('uniqueName', props['system_properties']['resource_subdomain'])
```
