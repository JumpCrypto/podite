from functools import partial
from io import BytesIO
from typing import Type

from podite._utils import _GetitemToCall, get_calling_module, get_concrete_type
from ..bytes import BYTES_CATALOG
from ..decorators import pod
from ..json import JSON_CATALOG, MISSING


def static_to_bytes_partial(packer, cls, buffer, obj, **kwargs):
    before = buffer.tell()
    packer(buffer, obj, **kwargs)
    after = buffer.tell()

    delta = after - before
    max_length = cls._calc_max_size()
    if delta > max_length:
        raise RuntimeError(
            f"The underlying type has consumed {delta} bytes > length ({max_length})"
        )

    if delta < max_length:
        buffer.write(bytes(max_length - delta))


def static_from_bytes_partial(unpacker, cls, buffer, **kwargs):
    before = buffer.tell()
    obj = unpacker(buffer, **kwargs)
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


def _static(name, type_: Type, length="auto"):
    module = get_calling_module()

    @pod
    class _Static:  # type: ignore
        @classmethod
        def _is_static(cls) -> bool:
            return True

        def _calc_size(self, **kwargs):
            return self.__class__._calc_max_size()

        @classmethod
        def _calc_max_size(cls):
            if length == "auto":
                return BYTES_CATALOG.calc_max_size(type_)
            else:
                return length

        @classmethod
        def _to_bytes_partial(cls, buffer, obj, **kwargs):
            static_to_bytes_partial(
                partial(BYTES_CATALOG.pack_partial, get_concrete_type(module, type_)),
                cls,
                buffer,
                obj,
                **kwargs,
            )

        @classmethod
        def _from_bytes_partial(cls, buffer, **kwargs):
            f = partial(BYTES_CATALOG.unpack_partial, get_concrete_type(module, type_))
            return static_from_bytes_partial(f, cls, buffer, **kwargs)

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

        def _calc_size(self, **kwargs):
            return BYTES_CATALOG.calc_size(get_concrete_type(module, type_), self)

        @classmethod
        def _calc_max_size(cls):
            return BYTES_CATALOG.calc_max_size(get_concrete_type(module, type_))

        @classmethod
        def _to_bytes_partial(cls, buffer, obj, **kwargs):
            return BYTES_CATALOG.pack_partial(
                get_concrete_type(module, type_), buffer, obj, **kwargs
            )

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO, **kwargs):
            return BYTES_CATALOG.unpack_partial(
                get_concrete_type(module, type_), buffer, **kwargs
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

        def _calc_size(self, **kwargs):
            return BYTES_CATALOG.calc_size(self.__class__.get_type(), self, **kwargs)

        @classmethod
        def _calc_max_size(cls):
            return BYTES_CATALOG.calc_max_size(cls.get_type())

        @classmethod
        def _to_bytes_partial(cls, buffer, obj, **kwargs):
            return BYTES_CATALOG.pack_partial(cls.get_type(), buffer, obj, **kwargs)

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO, **kwargs):
            return BYTES_CATALOG.unpack_partial(cls.get_type(), buffer, **kwargs)

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
