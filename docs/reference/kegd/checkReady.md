# Check Ready

This section describes the `checkReady` task available to use in the deployment strategies (`kegd.yaml` file).

Example:
```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
    checkReady:
      script: ready.py
```

## Arguments

### script

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| Y | - | N |

The file, from the `Lifecycle/kubernetes/scripts` directory of your Resource package, to use as a check ready script. This script must use Python syntax and must include the following `checkReady` function, with your desired implementation:

```python
def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    # Do the check here
    pass 
```

This function is the one called by the driver to perform the ready check. The arguments to this function are as follows:

| Name | Description |
| --- | --- |
| keg | A collection of all the objects deployed as part of this Resource (only those that still exist, so any objects that have been removed by a transition are not included) |
| props | A dictionary of all the properties available for this Resource. These are the same properties used when rendering templates |
| resultBuilder | Helper object for managing the result of the ready check | 
| log | Utility to log messages to (see more later) |
| *args and **kwargs | Python constructs for consuming any additional arguments passed to this function. You won't need to use them, so they are not required but it is highly recommended, as it will keep your scripts compatible with later versions of the driver if new arguments are added to this interface |

To walk through the creation of this file, see the [Ready Checks](../user-guide/ready-checks.md) section of the user guide.

### maxAttempts

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | - | `kegd.ready_checks.default_max_attempts` property value of the driver application (default is `10`) | N |

The maximum times the `checkReady` function is called before cancelling the transition and marking it as failed. This value should be a valid `int`. Special values include:

- `0` - no maximum attempts. Try only once.
- `-1` (or any negative value) - no limit to the attempts

There are no guarantees to how many times the check will be attempted, as the task is placed in a queue and may be dequeued at any time based on load.

### timeoutSeconds

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | - | `kegd.ready_checks.default_timeout_seconds` property value of the driver application (default is `300`) | N |

The amount of time that may pass, since the first ready check attempt, before the task is considered expired and the transition is marked as failed. This value should be a valid `int` and never `0` or below.

There are no guarantees the task will expire exactly after this time has passed, as the task is placed in a queue and may be dequeued at any time based on load. However, on dequeue, this value is checked and the next attempt is cancelled and no future attempts will be made.

### intervalSeconds

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | - | `kegd.ready_checks.default_interval_seconds` property value of the driver application (default is `5`) | N |

The amount of time that must pass before the next attempt. This is only a minimum, the next attempt may occur any time after this.

This value should be a valid `int` and '0' or below will result in no interval (although there will be an unknown interval based on load, as the task is queued and dequeued)
