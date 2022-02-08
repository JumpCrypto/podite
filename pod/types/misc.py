import inspect
from io import BytesIO
from typing import Type

from pod._utils import _GetitemToCall, get_calling_module, get_concrete_type
from ..bytes import BYTES_CATALOG
from ..json import JSON_CATALOG, MISSING
from ..decorators import pod


def _static(name, type_: Type, length="auto"):
    module = get_calling_module()

    @pod
    class _Static:  # type: ignore
        @classmethod
        def _is_static(cls) -> bool:
            return True

        @classmethod
        def _calc_max_size(cls):
            if length == "auto":
                return BYTES_CATALOG.calc_max_size(type_)
            else:
                return length

        @classmethod
        def _to_bytes_partial(cls, buffer, obj):
            before = buffer.tell()
            BYTES_CATALOG.pack_partial(get_concrete_type(module, type_), buffer, obj)
            after = buffer.tell()

            delta = after - before
            max_length = cls._calc_max_size()
            if delta > max_length:
                raise RuntimeError(
                    f"The underlying type has consumed {delta} bytes > length ({max_length})"
                )

            if delta < max_length:
                buffer.write(bytes(max_length - delta))

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO):
            before = buffer.tell()
            obj = BYTES_CATALOG.unpack_partial(
                get_concrete_type(module, type_), buffer
            )
            after = buffer.tell()

            delta = after - before
            max_length = cls._calc_max_size()
            if delta > max_length:
                raise RuntimeError(
                    f"The underlying type has consumed {delta} bytes > length ({max_length})"
                )

            if delta < max_length:
                required = max_length - delta
                if len(buffer.read(required)) < required:
                    raise RuntimeError("Bytes object was too small.")

            return obj

        @classmethod
        def _to_dict(cls, obj):
            return JSON_CATALOG.pack(get_concrete_type(module, type_), obj)

        @classmethod
        def _from_dict(cls, obj):
            return JSON_CATALOG.unpack(get_concrete_type(module, type_), obj)

    _Static.__name__ = f"{name}[{type_}, {length}]"
    _Static.__qualname__ = _Static.__name__

    return _Static


Static = _GetitemToCall("Static", _static)


def _default(name, type_: Type, default=None):
    module = get_calling_module()

    @pod(override=("from_bytes", "to_bytes"), dataclass_fn=None)
    class _Default:  # type: ignore
        @classmethod
        def _is_static(cls) -> bool:
            return BYTES_CATALOG.is_static(get_concrete_type(module, type_))

        @classmethod
        def _calc_max_size(cls):
            return BYTES_CATALOG.calc_max_size(get_concrete_type(module, type_))

        @classmethod
        def _to_bytes_partial(cls, buffer, obj):
            return BYTES_CATALOG.pack_partial(
                get_concrete_type(module, type_), buffer, obj
            )

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO):
            return BYTES_CATALOG.unpack_partial(
                get_concrete_type(module, type_), buffer
            )

        @classmethod
        def _to_dict(cls, obj):
            return JSON_CATALOG.pack(get_concrete_type(module, type_), obj)

        @classmethod
        def _from_dict(cls, obj):
            if obj is MISSING:
                if default is None:
                    return None
                return default()
            return JSON_CATALOG.unpack(get_concrete_type(module, type_), obj)

    _Default.__name__ = f"{name}[{type_}, {default}]"
    _Default.__qualname__ = _Default.__name__

    return _Default


# This can be used when the following elements don't have defaults.
# This is as opposed to `field` that has to come at the end.
Default = _GetitemToCall("Default", _default)


def _forward_ref(name, type_expr):
    module = get_calling_module()

    @pod(override=("from_bytes", "to_bytes"), dataclass_fn=None)
    class _ForwardRef:  # type: ignore
        type_ = None

        @classmethod
        def get_type(cls):
            if cls.type_ is None:
                cls.type_ = eval(
                    type_expr, {key: getattr(module, key) for key in dir(module)}
                )

            return cls.type_

        @classmethod
        def _is_static(cls) -> bool:
            return BYTES_CATALOG.is_static(cls.get_type())

        @classmethod
        def _calc_max_size(cls):
            return BYTES_CATALOG.calc_max_size(cls.get_type())

        @classmethod
        def _to_bytes_partial(cls, buffer, obj):
            return BYTES_CATALOG.pack_partial(cls.get_type(), buffer, obj)

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO):
            return BYTES_CATALOG.unpack_partial(cls.get_type(), buffer)

        @classmethod
        def _to_dict(cls, obj):
            return JSON_CATALOG.pack(cls.get_type(), obj)

        @classmethod
        def _from_dict(cls, obj):
            return JSON_CATALOG.unpack(cls.get_type(), obj)

    _ForwardRef.__name__ = f"{name}[{type_expr}]"
    _ForwardRef.__qualname__ = _ForwardRef.__name__

    return _ForwardRef


ForwardRef = _GetitemToCall("ForwardRef", _forward_ref)
