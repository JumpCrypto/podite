from io import BytesIO
from typing import Type

from ._utils import _GetitemToCall
from ..bytes import _BYTES_CATALOG
from ..json import _JSON_CATALOG, MISSING
from ..decorators import pod


def _static(name, type_: Type, length="auto"):

    if length == "auto":
        length = _BYTES_CATALOG.calc_max_size(type_)

    @pod
    class _Static:  # type: ignore
        @classmethod
        def _is_static(cls) -> bool:
            return True

        @classmethod
        def _calc_max_size(cls):
            return length

        @classmethod
        def _to_bytes_partial(cls, buffer, obj):
            before = buffer.tell()
            _BYTES_CATALOG.pack_partial(type_, buffer, obj)
            after = buffer.tell()

            delta = after - before
            if delta > length:
                raise RuntimeError(
                    f"The underlying type has consumed {delta} bytes > length ({length})"
                )

            if delta < length:
                buffer.write(bytes(length - delta))

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO):
            before = buffer.tell()
            obj = _BYTES_CATALOG.unpack_partial(type_, buffer)
            after = buffer.tell()

            delta = after - before
            if delta > length:
                raise RuntimeError(
                    f"The underlying type has consumed {delta} bytes > length ({length})"
                )

            if delta < length:
                buffer.read(length)

            return obj

        @classmethod
        def _to_json(cls, obj):
            return _JSON_CATALOG.pack(type_, obj)

        @classmethod
        def _from_json(cls, obj):
            return _JSON_CATALOG.unpack(type_, obj)

    _Static.__name__ = f"{name}[{type_}, {length}]"
    _Static.__qualname__ = _Static.__name__

    return _Static


Static = _GetitemToCall("Static", _static)


def _default(name, type_: Type, default=None):
    @pod(override=("from_bytes", "to_bytes"), dataclass_fn=None)
    class _Default:  # type: ignore
        @classmethod
        def _is_static(cls) -> bool:
            return _BYTES_CATALOG.is_static(type_)

        @classmethod
        def _calc_max_size(cls):
            return _BYTES_CATALOG.calc_max_size(type_)

        @classmethod
        def _to_bytes_partial(cls, buffer, obj):
            return _BYTES_CATALOG.pack_partial(type_, buffer, obj)

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO):
            return _BYTES_CATALOG.unpack_partial(type_, buffer)

        @classmethod
        def _to_json(cls, obj):
            return _JSON_CATALOG.pack(type_, obj)

        @classmethod
        def _from_json(cls, obj):
            if obj is MISSING:
                if default is None:
                    return None
                return default()
            return _JSON_CATALOG.unpack(type_, obj)

    _Default.__name__ = f"{name}[{type_}, {default}]"
    _Default.__qualname__ = _Default.__name__

    return _Default


Default = _GetitemToCall("Default", _default)
