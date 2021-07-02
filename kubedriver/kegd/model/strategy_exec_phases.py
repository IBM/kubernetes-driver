
class StrategyExecutionPhases:

    TASKS = 'Executing tasks'
    READY_CHECK = 'Executing ready check'
    RUN_SCRIPT = "Running script"
    OUTPUTS = 'Extracting outputs'
    IMMEDIATE_CLEANUP = 'Immediate cleanup'
    CLEANUP = 'Keg Cleanup'

    END = 'End'

    IMMEDIATE_CLEANUP_ON_FAILURE = 'Immediate cleanup on failure'