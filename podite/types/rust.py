from typing import Type
from functools import lru_cache

from podite._utils import _GetitemToCall, get_calling_module
from .enum import Enum, Variant, AutoTagType
from ..decorators import pod


def _option(_name, type_: Type):
    @pod
    class _Option(Enum[AutoTagType]):
        NONE = Variant()
        SOME = Variant(field=type_, module=get_calling_module(4))

    _Option.__name__ = f"Option[{type_}]"
    _Option.__qualname__ = _Option.__name__

    return _Option


Option = _GetitemToCall("Option", _option)
