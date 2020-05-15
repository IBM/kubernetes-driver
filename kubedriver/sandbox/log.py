
LIMIT = 100

class Log:

    def __init__(self, limit=LIMIT):
        self.__limit = limit
        self.__entries = []

    def entry(self, msg):
        self.__entries.append(str(msg))
        if len(self.__entries) > self.__limit:
            self.__entries.pop(0)

    def get_entries(self):
        return self.__entries.copy()

    def has_entries(self):
        return len(self.__entries) > 0

    def summarise(self):
        summary = 'Execution Log:'
        if len(self.__entries) == 0:
            summary += '\n\t<No Entries>'
        else:
            for entry in self.__entries:
                summary += f'\n\t{entry}'
        return summary