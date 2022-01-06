from typing import Type

from ._utils import _GetitemToCall
from .enum import Enum, Variant
from ..decorators import pod


def _option(_name, type_: Type):
    @pod
    class _Option(Enum):
        NONE = Variant()
        SOME = Variant(field=type_)

    _Option.__name__ = f"Option[{type_}]"
    _Option.__qualname__ = _Option.__name__

    return _Option


Option = _GetitemToCall("Option", _option)
