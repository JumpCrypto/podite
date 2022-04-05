import struct

from io import BytesIO
from typing import Literal

import podite.decorators as decorators
import podite._utils as utils

_BYTEORDER: Literal["little", "big"] = "little"


def new_atomic_type(name: str, base: type, code: str, unpacker, packer=lambda x: x):
    @decorators.pod(override=("from_bytes", "to_bytes"), dataclass_fn=None)
    class Atom(base):  # type: ignore
        @classmethod
        def _get_code(cls):
            order_char = "<" if _BYTEORDER == "little" else ">"
            return code.format(order_char)

        @classmethod
        def _is_static(cls) -> bool:
            return True

        @classmethod
        def _calc_size(cls, obj, **kwargs):
            return struct.calcsize(cls._get_code())

        @classmethod
        def _calc_max_size(cls):
            return struct.calcsize(cls._get_code())

        @classmethod
        def _to_bytes_partial(cls, buffer, obj, **kwargs):
            obj = packer(obj)
            buffer.write(struct.pack(cls._get_code(), obj))

        @classmethod
        def _from_bytes_partial(cls, buffer: BytesIO, **kwargs):
            size = cls._calc_max_size()
            encoded = buffer.read(size)
            decoded, *_ = struct.unpack(cls._get_code(), encoded)
            return unpacker(decoded)

        @classmethod
        def _to_dict(cls, obj):
            return obj

        @classmethod
        def _from_dict(cls, obj):
            return obj

    Atom.__name__ = name
    Atom.__qualname__ = name

    return Atom


def set_default_repr(repr_code):
    global _BYTEORDER
    _BYTEORDER = repr_code


def get_default_repr():
    return _BYTEORDER


# bool
Bool = new_atomic_type("Bool", object, "{}b", bool)


# 1-byte integers
I8l = new_atomic_type("I8l", int, "<b", int)
I8b = new_atomic_type("I8b", int, ">b", int)
I8 = new_atomic_type("I8", int, "{}b", int)

U8l = new_atomic_type("U8l", int, "<B", int)
U8b = new_atomic_type("U8b", int, ">B", int)
U8 = new_atomic_type("U8", int, "{}B", int)

# 2-byte integers
I16l = new_atomic_type("I16l", int, "<h", int)
I16b = new_atomic_type("I16b", int, ">h", int)
I16 = new_atomic_type("I16", int, "{}h", int)

U16l = new_atomic_type("U16l", int, "<H", int)
U16b = new_atomic_type("U16b", int, ">H", int)
U16 = new_atomic_type("U16", int, "{}H", int)


# 4-byte integers
I32l = new_atomic_type("I32l", int, "<i", int)
I32b = new_atomic_type("I32b", int, ">i", int)
I32 = new_atomic_type("I32", int, "{}i", int)

U32l = new_atomic_type("U32l", int, "<I", int)
U32b = new_atomic_type("U32b", int, ">I", int)
U32 = new_atomic_type("U32", int, "{}I", int)


# 8-byte integers
I64l = new_atomic_type("I64l", int, "<q", int)
I64b = new_atomic_type("I64b", int, ">q", int)
I64 = new_atomic_type("I64", int, "{}q", int)

U64l = new_atomic_type("U64l", int, "<Q", int)
U64b = new_atomic_type("U64b", int, ">Q", int)
U64 = new_atomic_type("U64", int, "{}Q", int)


# 16-byte integers
I128l = new_atomic_type(
    "I128l",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder="little", signed=True),
    packer=lambda x: int.to_bytes(x, length=16, byteorder="little", signed=True),
)
I128b = new_atomic_type(
    "I128b",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder="big", signed=True),
    packer=lambda x: int.to_bytes(x, length=16, byteorder="big", signed=True),
)
I128 = new_atomic_type(
    "I128",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder=_BYTEORDER, signed=True),
    packer=lambda x: int.to_bytes(x, length=16, byteorder=_BYTEORDER, signed=True),
)

U128l = new_atomic_type(
    "I128l",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder="little", signed=False),
    packer=lambda x: int.to_bytes(x, length=16, byteorder="little", signed=False),
)
U128b = new_atomic_type(
    "I128b",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder="big", signed=False),
    packer=lambda x: int.to_bytes(x, length=16, byteorder="big", signed=False),
)
U128 = new_atomic_type(
    "I128",
    int,
    "16s",
    unpacker=lambda x: int.from_bytes(x, byteorder=_BYTEORDER, signed=False),
    packer=lambda x: int.to_bytes(x, length=16, byteorder=_BYTEORDER, signed=False),
)

# Floating-point
F32l = new_atomic_type("F32l", float, "<f", float)
F32b = new_atomic_type("F32b", float, ">f", float)
F32 = new_atomic_type("F32", float, "{}f", float)

F64l = new_atomic_type("F64l", float, "<d", float)
F64b = new_atomic_type("F64b", float, ">d", float)
F64 = new_atomic_type("F64", float, "{}d", float)

# necessary to avoid cycles
utils.FORMAT_TO_TYPE[utils.FORMAT_BORSH] = U8
utils.FORMAT_TO_TYPE[utils.FORMAT_ZERO_COPY] = U64
