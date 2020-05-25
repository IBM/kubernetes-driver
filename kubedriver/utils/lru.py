import collections

class LRUCache:

    def __init__(self, capacity=100):
        self._cache = collections.OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key in self._cache:
            value = self._get_and_reorder_cache(key)
            return True, value
        else:
            return False, None

    def add(self, key, value):
        self._add_or_replace_in_cache(key, value)

    def _get_and_reorder_cache(self, key):
        value = self._cache.pop(key)
        self._cache[key] = value
        return value

    def _add_or_replace_in_cache(self, key, value):
        if key in self._cache:
            self._cache.pop(key)
        self._add_to_cache(key, value)

    def _add_to_cache(self, key, value):
        if len(self._cache) >= self.capacity:
            self._cache.popitem(last=False)
        self._cache[key] = value