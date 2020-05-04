## Indicate when objects created in this transition are ready
## systemProperties and resourceProperties included as the names of objects may have been templated with values from these maps

# Args:
# keg - provided python object to get Kubernetes objects
# systemProperties - generated system properties 
# resourceProperties - properties from the Resource
# resultBuilder - provided python object to use for returns
def ready(keg, systemProperties, resourceProperties, resultBuilder):
    job = keg.getObject('batch/v1', 'Job', systemProperties.resourceSubdomain + '-remove-entry')
    if job.status.succeeded == 1:
        return resultBuilder.ready()
    elif job.status.failed == 1:
        return resultBuilder.failed('this is why')
    else:
        return resultBuilder.notReady()
