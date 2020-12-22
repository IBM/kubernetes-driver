def getOutputs(keg, props, resultBuilder, log, *args, **kwargs):
    resultBuilder.setOutput('string', props['string_input'])
    resultBuilder.setOutput('integer', props['integer_input'])
    resultBuilder.setOutput('float', props['float_input'])
    resultBuilder.setOutput('timestamp', props['timestamp_input'])
    resultBuilder.setOutput('boolean', props['boolean_input'])
    resultBuilder.setOutput('map', props['map_input'])
    for k,v in props['map_input'].items():
        resultBuilder.setOutput('map_' + k, v)
    resultBuilder.setOutput('list', props['list_input'])
    i = 0
    for v in props['list_input']:
        resultBuilder.setOutput('list_' + str(i), v)
        i = i + 1
    resultBuilder.setOutput('custom', props['custom_input'])
    
    
    
    