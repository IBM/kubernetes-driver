# Ready Checks

If you've made it here then you should have already read [Building a Resource](building-a-resource.md) and have an idea of how to setup a Resource package and draft a deployment strategy (the kegd.yaml file).

As a basic example, you may have something like this:

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
      - objects:
          file: my-service.yaml
```

In `my-deployment.yaml` there is a extensions/v1beta1.Deployment or apps/v1.Deployment object and in `my-services.yaml` there is a v1.Service. On the `Create` transition for our Resource, the driver will deploy these objects to the target Kubernetes deployment location and complete successfully - but this doesn't mean our objects are ready for use. 

In Kubernetes, the act of deploying an object involves sending a desired configuration of an object, which the cluster API server will consume, validate and then persist in the cluster database (etcd) before returning a success response. In the background, a controller is notified of this new object and will attempt to update the cluster state to match your desired configuration.

In our example, when deploying `my-deployment.yaml`, Kubernetes will return successful if the object is valid and has been persisted. In the background, the Deployment controller will attempt to create the desired Pods. The Pods could fail on startup (maybe you forgot to load your Docker image into the right docker registry) but you wouldn't know unless you checked the `status` (`kubectl get deployment`).

In many cases, this asynchronous behaviour may be acceptable to you, however in some cases you may want to wait a while to check the cluster has updated correctly. This is a complex problem, as each object in Kubernetes has it's own definition of `status` and even if we come up with sensible checks for the most common object types, the definition of "ready" is unqiue to the context of your Resource. Plus, this wouldn't cover the potential for Custom Resources managed by operators.

Instead, the driver provides hooks for the Resource developer to plug-in scripts (with Python syntax) which may navigate the status of the objects deployed as part of the Resource to determine if they are ready. The script is allowed configurable retries, in order to poll the status of the objects over a period of time.

Each transition/operation may share or use different scripts or provide no script at all, in which case no ready checks are performed and the transition/operation is successful if the objects were accepted by Kubernetes.

**Table of Contents**:
- [Add a Ready Check Script](#add-a-ready-check-script)
- [Writing a Ready Check Script](#writing-a-ready-check-script)
  - [Keg](#keg)
  - [Props](#props)
  - [Result Builder](#result-builder)
  - [Log](#log)
  - [Complete Example](#complete-example)
  - [Return Key Properties](#return-key-properties)
- [Configuring Retries](#configuring-retries)

# Add a Ready Check Script

To add a ready check to your Resource, you will need to create a `scripts` directory in the `kubernetes` directory of your Resource:

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
      check-ready-on-create.py
    kegd.yaml
```

We'll talk about the contents of this file later. For now, configure the Create transition to use this script by modifying the `kegd.yaml` file. Add a `checkReady` field to the compose entry for Create and specify the name of your script.

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
```

Now, on a Create transition for this Resource, the driver will deploy the objects and then execute the `check-ready-on-create.py` script to inspect the objects.

# Writing a Ready Check Script

Ready check scripts are written in Python syntax but it's worth noting that you will not have the full power of the language at your disposal. For example, you won't be able to import modules and perform API calls out to external systems.

Instead, you will provide a `checkReady` function like so:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    # Do the work here
    pass 
```

This function is called by the driver to perform the ready check. The arguments to this function are as follows:

| Name | Description |
| --- | --- |
| keg | A collection of all the objects/helm releases deployed as part of this Resource (only those that still exist, so any objects that have been removed by a transition are not included) |
| props | A dictionary of all the properties available for this Resource. These are the same properties used when rendering templates |
| resultBuilder | Helper object for managing the result of the ready check | 
| log | Utility to log messages to (see more later) |
| *args and **kwargs | Python constructs for consuming any additional arguments passed to this function. You won't need to use them, so they are not required but it is highly recommended, as it will keep your scripts compatible with later versions of the driver if new arguments are added to this interface |

## Keg

The keg value can be used to retrieve objects (and helm releases) deployed as part of this Resource. This includes any objects deployed in earlier transitions/operations and the current one. Any objects removed in earlier transitions/operations or the current one are not included.

**Note:** objects marked with `immediateCleanup` are still available in the `keg` during the ready check and are only removed afterwards.

### Objects

Each object deployed directly (so without Helm) is retrievable by it's apiVersion (sometimes referred to as group), kind, name and namespace (if not a cluster wide type). For example, if in the `my-deployment.yaml` file you have deployed the following:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: Example
  namespace: demo
spec:
    ...spec data...
```

You can retrieve this object like so:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', 'Example', namespace='demo')
```

**Note:** this does not perform an API call on Kubernetes, the driver has already pre-fetched all the possible objects

The variable names `found` and `deployment` can be any valid Python variable name of your choosing. 

The value of `found` is a boolean (True/False) to indicate if the object is in the keg. When `False`, the value of `deployment` will be `None`. You should always check `found` before proceeding to use the value of `deployment`. 

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
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', 'Example', namespace='demo')
    if found:
        # deploymentName will equal 'Example'
        deploymentName = deployment['metadata']['name']
```

### Helm Releases

Each Helm release deployed is retrievable by it's name and namespace (Releases are actually different by their namespace but can have the same name in helm3).

As an example, if you've deployed a Helm chart in our kegd.yaml file:

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
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
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
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, helm_release = keg.helm_releases.get('MyReleaseName', 'MyNamespace')
    if found:
      objFound, controller = helm_release.objects.get('v1', 'Service', 'MyReleaseName-nginx-ingress-controller', namespace=helm_release.info['namespace'])
```

## Props

A dictionary of all the properties available for this Resource. These are included as they may be used when rendering templates, so if you've used them to configure identifying elements of an object, you will need them again to find it.

For example, if in the `my-deployment.yaml` file you have deployed the following:

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
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', props['system_properties']['resource_subdomain'], namespace='demo')
```

Check out the full range of [available properties](properties.md) later in the user guide.

## Result Builder

The `resultBuilder` allows you to inform the driver if the objects are ready or not. In fact, by default, the `resultBuilder` is set to believe everything is ready (the same default as when no script was provided) so it's ready check script's job to inform the driver this is not the case.

This means if you don't return anything, like below, the ready check will pass:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, deployment = keg.objects.get('apps/v1', 'Deployment', props['system_properties']['resource_subdomain'], namespace='demo')
    # Nothing else added, so the ready check passes
```

There are 3 states a ready check may return:
- Ready - all the objects are ok and the transition/operation may continue
- Not Ready - one or more objects are not ready, so do not continue and instead retry the ready check later (see more about retries later)
- Failed - there is an error that you believe will prevent the objects from ever being ready so the transition/operation should be failed

The `resultBuilder` includes functions to return each type:

```python
resultBuilder.ready()

resultBuilder.notReady() # or resultBuilder.not_ready()

resultBuilder.failed(reason)
```

You'll notice that when returning `failed` you must specify a reason (as a string) so this can be reported back to the user trying to install your Resource.

To set the status of the ready check, use `return` and one of the above functions at the appropriate time in your script:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    if someConditionWhichMeansFailure:
        return resultBuilder.failed('A useful error message')
    elif someConditionWhichMeansNotReady:
        return resultBuilder.notReady()
    
    # Not needed by good to add for clarity
    return resultBuilder.ready()
```

## Log

Allows you to return string messages back to the driver, which may included in any log or error messages produced by the driver related to this script. There is no requirement to use the `log` but it might be useful for debugging unexpected errors during execution. 

To add a new message to the log, use the `entry` function:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    log.entry('Log something useful')
```

The log is limited to 100 entries, any message added after reaching this limit will lead to the earliest message being removed.

## Complete example

Below is an academic example using all of the arguments together to produce a ready check script:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    deployment_name = props['system_properties']['resource_subdomain']
    found, deployment = keg.objects.get('apps/v1', 'Deployment', deployment_name, namespace='demo')

    if not found:
        return resultBuilder.failed(f'Could not find Deployment "{deployment_name}"')

    if 'status' not in deployment:
        log.entry(f'Waiting for status to be set on Deployment "{deployment_name}"')
        return resultBuilder.notReady()
    
    deployment_status = deployment['status']
    if 'availableReplicas' not in deployment_status:
        log.entry(f'Waiting for availableReplicas to be set on Deployment "{deployment_name}"')
        return resultBuilder.notReady()

    if deployment_status['availableReplicas'] <= 0:
        log.entry(f'Waiting for Deployment "{deployment_name}" to have available replicas')
        return resultBuilder.notReady()
    
    # availableReplicas is above 0, we are ready
    return resultBuilder.ready()
```

**What is this `f'Could not find Deployment...'` syntax?**: Python syntax to format a string with variables. Start a string with `f'` then reference a variable or function in the string to have it's value injected at runtime

# Configuring Retries

As seen earlier, you may return a `Not Ready` result on a ready check, which indicates the objects are not ready now but could be later. When the driver recieves this response, the transition/operation is paused and placed in a queue. Later, the transition/operation is dequeued and, if the configured interval time has passed, the driver will re-attempt the ready check.

This retry loop will continue until either:

- the maximum number of attempts are reached
- the time passed since the first attempt exceeds the timeout
- the ready check returns a failed or ready result

By default, the driver is configured with the following defaults:

- maxAttempts - 10
- timeoutSeconds - 300 (5 minutes)
- intervalSeconds - 5

The defaults can be changed globally for the driver through the application configuration properties.

In addition, you may set alternative values for your script. Do this by adding the values you want to override to the `checkReady` entry for your script in the `kegd.yaml` file in your Resource package. The following example overrides all 3 values but you can override each without the other:

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
      maxAttempts: 20
      timeoutSeconds: 60
      intervalSeconds: 2
```