

class ReadyCheckTask:

    def __init__(self, script, script_file_name):
        self.script = script
        self.script_file_name = script_file_name
    

    @staticmethod
    def on_read(script=None, scriptFileName=None):
        return ReadyCheckTask(script=script, script_file_name=scriptFileName)

    def on_write(self):
        return {
            'script': self.script,
            'scriptFileName': self.script_file_name
        }