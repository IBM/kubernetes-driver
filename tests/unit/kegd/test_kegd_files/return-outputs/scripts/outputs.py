def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    resultBuilder.setOutput('string', 'A string')
    resultBuilder.setOutput('integer', 123)
    resultBuilder.setOutput('float', 1.23)
    resultBuilder.setOutput('timestamp', '2020-11-24T11:49:33.305403Z')
    resultBuilder.setOutput('boolean', True)
    resultBuilder.setOutput('map', {'A': 1, 'B': 2})
    resultBuilder.setOutput('list', ['A', 'B'])
    resultBuilder.setOutput('custom', {'name': 'Testing', 'age': 42})
    
    
    
    