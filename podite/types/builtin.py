from typing import Optional, get_origin, Union, get_args, Any, ForwardRef

from podite.bytes import BytesPodConverter, BYTES_CATALOG
from podite.json import JsonPodConverter, JSON_CATALOG

from .atomic import U64


class BoolConverter(BytesPodConverter, JsonPodConverter):
    def get_mapping(self, type_):
        if type_ == bool:
            return self

        return None

    def is_static(self, type_) -> bool:
        return True

    def calc_size(self, type_, **kwargs) -> int:
        return 1

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

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        return obj

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        return obj


class StrConverter(BytesPodConverter, JsonPodConverter):
    def get_mapping(self, type_):
        if type_ == str:
            return self

        return None

    def is_static(self, type_) -> bool:
        return False

    def calc_size(self, type_, obj, **kwargs) -> int:
        return 8 + len(obj)

    def calc_max_size(self, type_) -> int:
        return 2**64 + 8

    def pack_partial(self, type_, buffer, obj, **kwargs):
        BYTES_CATALOG.pack_partial(U64, buffer, len(obj))
        buffer.write(obj.encode("utf-8"))

    def unpack_partial(self, type_, buffer, **kwargs) -> bool:
        length = BYTES_CATALOG.unpack_partial(U64, buffer)

        return buffer.read(length).decode("utf-8")

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        return obj

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        return obj


class OptionalConverter(BytesPodConverter, JsonPodConverter):
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
        field_type = get_args(type_)[0]
        if isinstance(field_type, ForwardRef):
            raise RuntimeError("ForwardRef is not currently supported in Optional.")
        return field_type

    def is_static(self, type_) -> bool:
        return False

    def calc_size(self, type_, obj, **kwargs) -> int:
        field_type = self.get_field_type(type_)
        return 1 + BYTES_CATALOG.calc_size(field_type)

    def calc_max_size(self, type_) -> int:
        field_type = self.get_field_type(type_)
        return 1 + BYTES_CATALOG.calc_max_size(field_type)

    def pack_partial(self, type_, buffer, obj, **kwargs):
        if obj is None:
            buffer.write(b"\x00")
        else:
            buffer.write(b"\x01")

            field_type = self.get_field_type(type_)
            BYTES_CATALOG.pack_partial(field_type, buffer, obj, **kwargs)

    def unpack_partial(self, type_, buffer, **kwargs):
        b = buffer.read(1)
        if len(b) == 0:
            raise ValueError("The end of the buffer reached but requires 1 bytes")

        if b not in (b"\x00", b"\x01"):
            raise ValueError("Invalid byte")

        if b == b"\x00":
            return None

        field_type = self.get_field_type(type_)
        return BYTES_CATALOG.unpack_partial(field_type, buffer, **kwargs)

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        if obj is None:
            return None
        return JSON_CATALOG.pack(self.get_field_type(type_), obj)

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        if obj is None:
            return None
        return JSON_CATALOG.unpack(self.get_field_type(type_), obj)


class TupleConverter(BytesPodConverter, JsonPodConverter):
    def get_mapping(self, type_):
        if get_origin(type_) == tuple:
            return self

        return None

    def is_static(self, type_) -> bool:
        catalog = BYTES_CATALOG
        for arg in get_args(type_):
            if not catalog.is_static(arg):
                return False
        return True

    def calc_size(self, type_, obj, **kwargs) -> int:
        total = 0
        for obj, arg_type in zip(obj, get_args(type_)):
            total += BYTES_CATALOG.calc_size(arg_type, obj, **kwargs)

        return total

    def calc_max_size(self, type_) -> int:
        catalog = BYTES_CATALOG

        total = 0
        for arg in get_args(type_):
            total += catalog.calc_max_size(arg)

        return total

    def pack_partial(self, type_, buffer, obj, **kwargs):
        fields_types = get_args(type_)
        if not isinstance(obj, tuple):
            raise ValueError(f"Expected a tuple, but received a {type(obj)}")

        if len(obj) != len(fields_types):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        for e, t in zip(obj, fields_types):
            BYTES_CATALOG.pack_partial(t, buffer, e, **kwargs)

    def unpack_partial(self, type_, buffer, **kwargs):
        fields_types = get_args(type_)
        return tuple(
            BYTES_CATALOG.unpack_partial(t, buffer, **kwargs) for t in fields_types
        )

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        fields_types = get_args(type_)
        if not isinstance(obj, tuple):
            raise ValueError(f"Expected a tuple, but received a {type(obj)}")

        if len(obj) != len(fields_types):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        return tuple(JSON_CATALOG.pack(t, e) for e, t in zip(obj, fields_types))

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        fields_types = get_args(type_)
        if len(fields_types) != len(obj):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        return tuple(
            JSON_CATALOG.unpack(t, e, **kwargs) for t, e in zip(fields_types, obj)
        )


class JsonIdentityPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        if type_ in (int, str, object):
            return self

        return None

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        return obj

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        return obj


class JsonBytesPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        if type_ == bytes:
            return self

        return None

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        return list(obj)

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        return bytes(obj)


class JsonListConverter(JsonPodConverter):
    def get_mapping(self, type_):
        if get_origin(type_) == list:
            return self

        return None

    @staticmethod
    def get_field_type(type_):
        return get_args(type_)[0]

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        field_type = self.get_field_type(type_)
        return [JSON_CATALOG.pack(field_type, e) for e in obj]

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        field_type = self.get_field_type(type_)
        return [JSON_CATALOG.unpack(field_type, e) for e in obj]


def register_builtins():
    BYTES_CATALOG.register(BoolConverter().get_mapping)
    BYTES_CATALOG.register(StrConverter().get_mapping)
    BYTES_CATALOG.register(OptionalConverter().get_mapping)
    BYTES_CATALOG.register(TupleConverter().get_mapping)

    JSON_CATALOG.register(BoolConverter().get_mapping)
    JSON_CATALOG.register(StrConverter().get_mapping)
    JSON_CATALOG.register(OptionalConverter().get_mapping)
    JSON_CATALOG.register(TupleConverter().get_mapping)
    JSON_CATALOG.register(JsonIdentityPodConverter().get_mapping)
    JSON_CATALOG.register(JsonBytesPodConverter().get_mapping)
    JSON_CATALOG.register(JsonListConverter().get_mapping)
