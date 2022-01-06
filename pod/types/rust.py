from typing import Type

from . import U32
from ._utils import _GetitemToCall
from .enum import Enum, Variant, _ENUM_PACKED
from ..decorators import pod


def _option(_name, type_: Type, packed: bool = True):
    @pod
    class _Option(Enum):
        NONE = Variant()
        SOME = Variant(field=type_)

    _Option.__name__ = f"Option[{type_}]"
    _Option.__qualname__ = _Option.__name__

    setattr(_Option, _ENUM_PACKED, packed)

    return _Option


Option = _GetitemToCall("Option", _option)
