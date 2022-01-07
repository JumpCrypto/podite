from typing import Optional, get_origin, Union, get_args, Any

from pod import get_catalog
from pod.bytes import BytesPodConverter, _BYTES_CATALOG
from pod.json import JsonPodConverter, _JSON_CATALOG


class BoolConverter(BytesPodConverter, JsonPodConverter):
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

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        return obj

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
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
        return get_args(type_)[0]

    def is_static(self, type_) -> bool:
        return False

    def calc_max_size(self, type_) -> int:
        field_type = self.get_field_type(type_)
        return 1 + _BYTES_CATALOG.calc_max_size(field_type)

    def pack_partial(self, type_, buffer, obj, **kwargs):
        if obj is None:
            buffer.write(b"\x00")
        else:
            buffer.write(b"\x01")

            field_type = self.get_field_type(type_)
            _BYTES_CATALOG.pack_partial(field_type, buffer, obj)

    def unpack_partial(self, type_, buffer, **kwargs):
        b = buffer.read(1)
        if len(b) == 0:
            raise ValueError("The end of the buffer reached but requires 1 bytes")

        if b not in (b"\x00", b"\x01"):
            raise ValueError("Invalid byte")

        if b == b"\x00":
            return None

        field_type = self.get_field_type(type_)
        return _BYTES_CATALOG.unpack_partial(field_type, buffer)

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        if obj is None:
            return None
        return _JSON_CATALOG.pack(self.get_field_type(type_), obj)

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        if obj is None:
            return None
        return _JSON_CATALOG.unpack(self.get_field_type(type_), obj)


class TupleConverter(BytesPodConverter, JsonPodConverter):
    def get_mapping(self, type_):
        if get_origin(type_) == tuple:
            return self

        return None

    def is_static(self, type_) -> bool:
        catalog = _BYTES_CATALOG
        for arg in get_args(type_):
            if not catalog.is_static(arg):
                return False
        return True

    def calc_max_size(self, type_) -> int:
        catalog = _BYTES_CATALOG

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
            _BYTES_CATALOG.pack_partial(t, buffer, e)

    def unpack_partial(self, type_, buffer, **kwargs):
        fields_types = get_args(type_)
        return tuple(
            _BYTES_CATALOG.unpack_partial(t, buffer, **kwargs) for t in fields_types
        )

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        fields_types = get_args(type_)
        if not isinstance(obj, tuple):
            raise ValueError(f"Expected a tuple, but received a {type(obj)}")

        if len(obj) != len(fields_types):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        return tuple(_JSON_CATALOG.pack(t, e) for e, t in zip(obj, fields_types))

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        fields_types = get_args(type_)
        if len(fields_types) != len(obj):
            raise ValueError(f"Tuple should have exactly {len(fields_types)} elements")

        return tuple(
            _JSON_CATALOG.unpack(t, e, **kwargs) for t, e in zip(fields_types, obj)
        )


class JsonIdentityPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        if type_ in (int, str):
            return self

        return None

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        return obj

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        return obj


class JsonBytesPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        if type_ == bytes:
            return self

        return None

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        return list(obj)

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        return bytes(obj)


def register_builtins():
    _BYTES_CATALOG.register(BoolConverter().get_mapping)
    _BYTES_CATALOG.register(OptionalConverter().get_mapping)
    _BYTES_CATALOG.register(TupleConverter().get_mapping)

    _JSON_CATALOG.register(BoolConverter().get_mapping)
    _JSON_CATALOG.register(OptionalConverter().get_mapping)
    _JSON_CATALOG.register(TupleConverter().get_mapping)
    _JSON_CATALOG.register(JsonIdentityPodConverter().get_mapping)
    _JSON_CATALOG.register(JsonBytesPodConverter().get_mapping)
