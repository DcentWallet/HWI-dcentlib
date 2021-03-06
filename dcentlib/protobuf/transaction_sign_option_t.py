# Automatically generated by pb2py
# fmt: off
from .. import prototrez as p

if __debug__:
    try:
        from typing import Dict, List  # noqa: F401
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        pass


class transaction_sign_option_t(p.MessageType):

    def __init__(
        self,
        param_data: bytes = None,
    ) -> None:
        self.param_data = param_data

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('param_data', p.BytesType, 0),  # required
        }
