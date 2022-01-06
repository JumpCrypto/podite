from typing import Optional, get_origin, Union, get_args

from pod import get_catalog
from pod.bytes import BytesPodConverter


class BoolConverter(BytesPodConverter):
    def get_mapping(self, type_):
        if type_ == bool:
            return self

        return None

    def is_static(self, type_) -> bool:
        return True

    def calc_max_size(self, type_) -> int:
        return 1

    def pack_partial(self, type_, buffer, obj, **kwargs):
        buffer.write(bytes(obj))

    def unpack_partial(self, type_, buffer, **kwargs) -> bool:
        b = buffer.read(1)
        if len(b) == 0:
            raise ValueError("The end of the buffer reached but requires 1 bytes")

        if b not in (b"\x00", b"\x01"):
            raise ValueError("Invalid byte")

        return b == b"\x01"


class OptionalConverter(BytesPodConverter):
    def get_mapping(self, type_):
        if type_ == Optional:
            raise ValueError("Optional must be bound with type for byte conversions")

        if get_origin(type_) == Union:
            args = get_args(type_)
            if len(args) == 2 and issubclass(args[1], type(None)):
                return self

        return None

    @staticmethod
    def get_field_type(type_):
        return get_args(type_)[0]

    def is_static(self, type_) -> bool:
        return False

    def calc_max_size(self, type_) -> int:
        field_type = self.get_field_type(type_)
        return 1 + get_catalog("bytes").calc_max_size(field_type)

    def pack_partial(self, type_, buffer, obj, **kwargs):
        if obj is None:
            buffer.write(b"\x00")
        else:
            buffer.write(b"\x01")

            field_type = self.get_field_type(type_)
            get_catalog("bytes").pack_partial(field_type, buffer, obj)

    def unpack_partial(self, type_, buffer, **kwargs):
        b = buffer.read(1)
        if len(b) == 0:
            raise ValueError("The end of the buffer reached but requires 1 bytes")

        if b not in (b"\x00", b"\x01"):
            raise ValueError("Invalid byte")

        if b == b"\x00":
            return None

        field_type = self.get_field_type(type_)
        return get_catalog("bytes").unpack_partial(field_type, buffer)


class TupleConverter(BytesPodConverter):
    def get_mapping(self, type_):
        if get_origin(type_) == tuple:
            return self

        return None

    def is_static(self, type_) -> bool:
        catalog = get_catalog("bytes")
        for arg in get_args(type_):
            if not catalog.is_static(arg):
                return False
        return True

    def calc_max_size(self, type_) -> int:
        catalog = get_catalog("bytes")

        total = 0
        for arg in get_args(type_):
            total += catalog.calc_max_size(arg)

        return total

    def pack_partial(self, type_, buffer, obj, **kwargs):
        fields_types = get_args(type_)
        if isinstance(obj, tuple):
            raise ValueError(f"Expected a tuple, but received a {type(obj)}")

        if len(obj) != len(fields_types):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        catalog = get_catalog("bytes")
        for e, t in zip(obj, fields_types):
            catalog.pack_partial(t, buffer, e)

    def unpack_partial(self, type_, buffer, **kwargs):
        fields_types = get_args(type_)
        catalog = get_catalog("bytes")
        return tuple(catalog.unpack_partial(t, buffer, **kwargs) for t in fields_types)


def register_builtins():
    get_catalog("bytes").register(BoolConverter().get_mapping)
    get_catalog("bytes").register(OptionalConverter().get_mapping)
    get_catalog("bytes").register(TupleConverter().get_mapping)
