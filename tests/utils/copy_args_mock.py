import copy
from unittest.mock import MagicMock

class CopyArgsMagicMock(MagicMock):
    def _mock_call(self, *args, **kwargs):
        """
        Store copies of arguments passed into calls to the
        mock object, instead of storing references to the original argument objects.
        """
        return super()._mock_call(*copy.deepcopy(args), **copy.deepcopy(kwargs))
