## Gather outputs from objects
## systemProperties and resourceProperties included as the names of objects may have been templated with values from these maps

# Args:
# keg - provided python object to get Kubernetes objects
# outputs - provided python object to add the outputs to
def getOutputs(keg, systemProperties, resourceProperties, outputs):
    deployment = keg.getObject('v1', 'Deployment', systemProperties.resourceSubdomain)
    outputs.add('someProp', deployment.status.someProp)
    outputs.add('someOtherProp', deployment.status.someOtherProp)