# Get Outputs

This section describes the `getOutputs` task available to use in the deployment strategies (`kegd.yaml` file).

Example:

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
    getOutputs:
      script: get-outputs.py
```

## Arguments

### script

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| Y | - | N |

The file, from the `Lifecycle/kubernetes/scripts` directory of your Resource package, to use as an output extraction script. This script must use Python syntax and must include the following `getOutputs` function, with your desired implementation:

```python
def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    # Do the check here
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

You may also specify the file value as the only argument to the `getOutputs` task:

```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
    # read as value of `script`
    getOutputs: get-outputs.py 
```

To walk through the creation of this file, see the [Extracting Outputs](../user-guide/extracting-outputs.md) section of the user guide.

