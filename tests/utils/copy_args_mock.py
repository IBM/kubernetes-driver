import copy
from unittest.mock import MagicMock

class CopyArgsMagicMock(MagicMock):
    def __call__(self, *args, **kwargs):
        """
        Store copies of arguments passed into calls to the
        mock object, instead of storing references to the original argument objects.
        """
        return super().__call__(*copy.deepcopy(args), **copy.deepcopy(kwargs))
