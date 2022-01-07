from io import BytesIO
from typing import Type

from ._utils import _GetitemToCall
from ..bytes import _BYTES_CATALOG
from ..json import _JSON_CATALOG
from ..decorators import pod


def _static(name, type_: Type, length="auto"):

    if length == "auto":
        length = _BYTES_CATALOG.calc_max_size(type_)

    @pod(override=("from_bytes", "to_bytes"), dataclass_fn=None)
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
