# Objects

This section describes the `objects` task available to use in the `deploy` section of a deployment strategy (`kegd.yaml` file).

Example:
```
compose:
  - name: Create
    deploy:
      - objects:
          file: my-deployment.yaml
```

## Arguments

### file

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| Y | - | Y (see [templating values](#templating-values)) |

The file, from the `Lifecycle/kubernetes/objects` directory of your Resource package, which describes the objects to be deployed in the [Kubernetes object configuration file format](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/). The file may feature multiple objects separated by the YAML document separator (see [example object configuration](#example-configuration.md)). This file will be rendered as template, so you may inject properties into this file as described in [templating](../user-guide/templating.md)

### immediateCleanupOn

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | Never | N |

Request that the objects deployed are immediately removed at the end of the transition execution (so after ready checks and output extraction).

Possible values for this setting include: 
- Never - the default behaviour, to keep the object until the cleanupOn settings dictate it should be removed 
- Success - the object should be removed after the transition/operation completes successfully 
- Failure - the object should be removed only if the transition/operation fails
- Always - always remove the object at the end of the transition/operation regardless of the result.

A transition is considered "complete" enough to run immediate cleanup after the following phases are complete:

- Removal of any objects that should be removed on this transition/operation
- Deployed objects that are scheduled to on this transition/operation
- Ready check completed successfully 
- Output extraction completed successfully

If a failure occurs during the immediate cleanup, the transition/operation will be marked as failed.

## Templating Values

Example kegd.yaml which uses the value of a `fileToUse` property on the Resource descriptor to specify the template:
```
compose:
  - name: Create
    deploy:
      - objects:
          file: "{{ fileToUse }}"
```

## Example Object Configuration

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