from dataclasses import is_dataclass, fields
from io import BytesIO
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Callable, Any

from .core import PodConverterCatalog


class BytesPodConverter(ABC):
    @abstractmethod
    def is_static(self, type_) -> Tuple[bool, bool]:
        raise NotImplementedError

    @abstractmethod
    def calc_max_size(self, type_) -> Tuple[bool, int]:
        raise NotImplementedError

    @abstractmethod
    def pack_partial(self, type_, buffer, obj, **kwargs) -> Tuple[bool, Any]:
        raise NotImplementedError

    @abstractmethod
    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        raise NotImplementedError


IS_STATIC = "_is_static"
CALC_MAX_SIZE = "_calc_max_size"
TO_BYTES_PARTIAL = "_to_bytes_partial"
FROM_BYTES_PARTIAL = "_from_bytes_partial"


class CustomBytesPodConverter(BytesPodConverter):
    @staticmethod
    def _call_by_name(type_, name, args, kwargs, default_value):
        if not hasattr(type_, name):
            return False, default_value

        method = getattr(type_, name)
        return True, method(*args, **kwargs)

    def is_static(self, type_) -> Tuple[bool, bool]:
        return self._call_by_name(type_, IS_STATIC, (), {}, False)

    def calc_max_size(self, type_) -> Tuple[bool, int]:
        return self._call_by_name(type_, CALC_MAX_SIZE, (), {}, 0)

    def pack_partial(self, type_, buffer, obj, **kwargs) -> Tuple[bool, Any]:
        args = (buffer, obj)
        return self._call_by_name(type_, TO_BYTES_PARTIAL, args, kwargs, None)

    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        return self._call_by_name(
            type_,
            FROM_BYTES_PARTIAL,
            (buffer,),
            kwargs,
            None,
        )


class BytesPodConverterCatalog(PodConverterCatalog[BytesPodConverter]):
    def is_static(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = "No converter was able to answer if this obj is static"
        return self._call_until_success("is_static", (type_,), {}, error_msg)

    def calc_max_size(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = "No converter was able to calculate maximum size of obj"
        return self._call_until_success("calc_max_size", (type_,), {}, error_msg)

    def pack(self, type_, obj, **kwargs):
        buffer = BytesIO()
        self.pack_partial(type_, buffer, obj, **kwargs)

        return buffer.getvalue()

    def pack_partial(self, type_, buffer, obj, **kwargs):
        args = type_, buffer, obj
        error_msg = "No converter was able to unpack raw data"
        self._call_until_success("pack_partial", args, kwargs, error_msg)

    def unpack(self, type_, raw, checked=False, **kwargs) -> object:
        buffer = BytesIO(raw)
        obj = self.unpack_partial(type_, buffer, **kwargs)

        if checked and buffer.tell() < len(buffer.getvalue()):
            raise RuntimeError("Unused bytes in provided raw data")

        return obj

    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        args = type_, buffer
        error_msg = "No converter was able to pack object"
        return self._call_until_success("unpack_partial", args, kwargs, error_msg)

    def generate_helpers(self, type_) -> Dict[str, Callable]:
        helpers = super().generate_helpers(type_)

        @classmethod  # type: ignore[misc]
        def is_static(cls):
            return _BYTES_CATALOG.is_static(cls)

        @classmethod  # type: ignore[misc]
        def calc_max_size(cls):
            return _BYTES_CATALOG.calc_max_size(cls)

        @classmethod  # type: ignore[misc]
        def calc_size(cls):
            if not cls.is_static():
                raise RuntimeError("calc_size can only be called for static classes")

            return cls.calc_max_size()

        @classmethod  # type: ignore[misc]
        def to_bytes(cls, obj, **kwargs):
            return cls.pack(obj, converter="bytes", **kwargs)

        @classmethod  # type: ignore[misc]
        def from_bytes(cls, raw, **kwargs):
            return cls.unpack(raw, converter="bytes", **kwargs)

        helpers["is_static"] = is_static
        helpers["calc_max_size"] = calc_max_size
        helpers["calc_size"] = calc_size
        helpers["to_bytes"] = to_bytes
        helpers["from_bytes"] = from_bytes

        if is_dataclass(type_):
            helpers.update(self._generate_packers())

        return helpers

    def _generate_packers(self) -> Dict[str, Callable]:
        helpers: Dict[str, Callable] = {}

        @classmethod  # type: ignore[misc]
        def _is_static(cls) -> bool:
            for field in fields(cls):
                if not self.is_static(field.type):
                    return False
            return True

        @classmethod  # type: ignore[misc]
        def _calc_max_size(cls):
            total = 0
            for field in fields(cls):
                total += self.calc_max_size(field.type)

            return total

        @classmethod  # type: ignore[misc]
        def _to_bytes_partial(cls, buffer, obj):
            for field in fields(cls):
                value = getattr(obj, field.name)
                self.pack_partial(field.type, buffer, value)

        @classmethod  # type: ignore[misc]
        def _from_bytes_partial(cls, buffer, **kwargs):
            values = {}
            for field in fields(cls):
                values[field.name] = self.unpack_partial(field.type, buffer)
            return cls(**values)

        helpers[IS_STATIC] = _is_static
        helpers[CALC_MAX_SIZE] = _calc_max_size
        helpers[TO_BYTES_PARTIAL] = _to_bytes_partial
        helpers[FROM_BYTES_PARTIAL] = _from_bytes_partial

        return helpers


_BYTES_CATALOG = BytesPodConverterCatalog()
_BYTES_CATALOG.register(CustomBytesPodConverter())
