# Extracting Outputs 

If you've made it here then you should have already read [Building a Resource](building-a-resource.md) and have an idea of how to setup a resource package and draft a deployment strategy (the kegd.yaml file).

It's good to also have an understanding of [Ready Checks](ready-checks.md) as this is executed before any outputs can be extracted.

Outputs are property values you would like to return on any lifecycle transition/operation request. These values are consumed by Brent and stored on the resource. Subsequent transition/operation requests can then reference these values as properties in templates and/or scripts. If the property exists on the resource descriptor, then the value will be visible in the ALM topology and can be mapped to other resources in an Assembly design (note: only outputs set on Create or Install transitions will be consumed by the ALM topology).

Usually, you will want to retrieve a value from an object to use as an output value and, in most cases, this field will come from the `status` field of the object. In [Ready Checks](ready-checks.md) we discussed how every object in Kubernetes has a different definition for it's `status` (and `spec` too but those are usually inputs). 

As a result, the driver provides hooks for the resource developer to plug-in scripts (with Python syntax) which may navigate the status of the objects deployed as part of the resource to extract outputs. This script is only executed after the ready check has passed (when no ready check exists the outputs are extracted immediately after the objects have been deployed).

Unlike the scripts used for ready checks, the output extraction script is only executed once for a transition/operation.

Each transition/operation may share or use different scripts or provide no script at all, in which case no outputs are extracted.

**Table of Contents**:
- [Add an Output Extraction Script](#add-an-output-extraction-script)
- [Writing an Output Extraction Script](#writing-an-output-extraction-script)
  - [Result Builder](#result-builder)
  - [Complete Example](#complete-example)
  - [Return Key Properties](#return-key-properties)

# Add an Output Extraction Script

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

We'll talk about the contents of this file later. For now, configure the Create transition to use this script by modifying the `kegd.yaml` file. Add a `getOutputs` field to the compose entry for Create and specify the name of your script.

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

# Writing an Output Extraction Script

Output extraction scripts are written in Python syntax but it's worth noting that you will not have the full power of the language at your disposal. For example, you won't be able to import modules and perform API calls out to external systems.

Instead, you will provide a `getOutputs` function like so:

```
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    # Do the work here
    pass 
```

This function is called by the driver to perform the output extraction. The arguments to this function are as follows:

| Name | Description |
| --- | --- |
| keg | A collection of all the objects/helm releases deployed as part of this resource (only those that still exist, so any objects that have been removed by a transition are not included) |
| props | A dictionary of all the properties available for this resource. These are the same properties used when rendering templates |
| resultBuilder | Helper object for managing the result | 
| log | Utility to log messages to (see more later) |
| *args and **kwargs | Python constructs for consuming any additional arguments passed to this function. You won't need to use them, so they are not required but it is highly recommended, as it will keep your scripts compatible with later versions of the driver if new arguments are added to this interface |

The values of `keg`, `props` and `log` are the same ones used in [ready checks](ready-checks.md#writing-a-ready-check-script), so refer to that section of the user guide to recap them.

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

## Return Key Properties

If you create a key as part of your Keg (maybe in a Secret or through a Job) you can return them as outputs so they may be stored in Brent. They can then later be used in other transitions executed, even if that transition is handled by another drivers (maybe you need this key for an ansible playbook).

To do this, you must return the name of the key, the public key and private key as a single value for the intended property (a property with `type: key` in the Resource descriptor). 

The value must be formatted as one of the below options:
```
<key_name>#<private_key>#<public_key>

#Return just a private key (note the trailing #)
<key_name>#<private_key>#

#Return just a public key (note the double #)
<key_name>##<public_key>
```

As an example, if you have a Resource descriptor property, of type `key`, named `myKey` and you've deployed a Config Map with the key values as below (real public and private keys are not included to keep the code snippet short):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mykey
type: Opaque
stringData:
  keyName: someKey
  privateKey: the private part
  publicKey: the public part
```

You can find the ConfigMap and return the values as outputs like so:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, configmap = keg.objects.get('v1', 'ConfigMap', 'mykey', namespace='demo')
    if not found:
        return resultBuilder.failed('Could not find config map named mykey')
    data = configmap['data']
    keyValue = data['keyName'] + '#' + data['privateKey'] + '#' + data['publicKey']
    resultBuilder.setOutput('mykey', keyValue)
```

It's much safer to store sensitive values such as keys inside Secrets. When you do this, they will base64 encoded and you'll want to decode them before returning them as outputs. 

The `resultBuilder` object includes a `decode` function to help base64 decode the values based on your chosen encoding (by default `'utf-8'`). For example, if you've deployed a Secret with the key values (real public and private keys are not included to keep the code snippet short):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysecretkey
type: Opaque
stringData:
  keyName: someKey
  publicKey: the public part
  privateKey: the private part
```

**Note:** `stringData` is a ["write-only convenience field"](https://kubernetes.io/docs/concepts/configuration/secret/#creating-a-secret-manually) you may use to pass non-encoded data to a Secret and it will be encoded for you. To read the values back you will need to use `data`.

You can now find the Secret, decode the values and return them as outputs like so:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    found, secret = keg.objects.get('v1', 'Secret', 'mysecretkey', namespace='demo')
    if not found:
        return resultBuilder.failed('Could not find secret named mysecretkey')
    data = secret['data']
    keyName = resultBuilder.decode(data['keyName'])
    privateKey = resultBuilder.decode(data['privateKey'])
    publicKey = resultBuilder.decode(data['publicKey'])
    keyValue = keyName + '#' + privateKey + '#' + publicKey
    resultBuilder.setOutput('mykey', keyValue)
```

**Note:** notice how the example decodes each part separately before concatenating them. This is important as if you decode them after they may not be correct.

Read more on keys in the ALM documentation: 

- [Infrastructure Keys](http://servicelifecyclemanager.com/2.1.0/reference/lm-api/api-definition/resource-manager/infrastructure-keys/)
- [Infrastructure Keys Example](http://servicelifecyclemanager.com/2.1.0/user-guides/resource-engineering/resource-packages/brent/infrastructure-keys-resource/get-started/)

# Next Steps

If you've followed the guide in order then you should now have an understanding of how to deploy objects and/or helm charts, check they are ready and return attributes from them as outputs. 

You can read more about the syntax for output scripts in the [Kegd Reference](reference/kegd/index.md). 

Otherwise, proceed with [Templating](templating.md) and [Available Properties](available-properties.md) to read more about using Resource properties in your deployment templates and scripts. 