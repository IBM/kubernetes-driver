
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