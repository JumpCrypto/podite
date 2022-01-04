from io import BytesIO
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Callable

from .core import PodConverter, PodConverterCatalog


class BytesPodConverter(PodConverter, ABC):
    @abstractmethod
    def is_static(self, type_) -> Tuple[bool, bool]:
        raise NotImplementedError

    @abstractmethod
    def calc_max_size(self, type_) -> Tuple[bool, int]:
        raise NotImplementedError

    def pack(self, type_, obj, **kwargs) -> Tuple[bool, bytes]:
        buffer = BytesIO()
        success = self.pack_partial(type_, buffer, obj, **kwargs)

        return success, buffer.getvalue()

    @abstractmethod
    def pack_partial(self, type_, buffer, obj, **kwargs) -> bool:
        raise NotImplementedError

    def unpack(self, type_, raw, checked=False, **kwargs) -> Tuple[bool, object]:
        buffer = BytesIO(raw)
        success, obj = self.unpack_partial(type_, buffer, **kwargs)

        if success and checked:
            if buffer.tell() < len(buffer.getvalue()):
                raise RuntimeError("Unused bytes in provided raw data")

        return success, obj

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

    def pack_partial(self, type_, buffer, obj, **kwargs) -> bool:
        args = (type_, buffer, obj)
        return self._call_by_name(type_, TO_BYTES_PARTIAL, args, kwargs, None)[0]

    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        return self._call_by_name(
            type_,
            FROM_BYTES_PARTIAL,
            (
                type_,
                buffer,
            ),
            kwargs,
            None,
        )


class BytesPodConverterCatalog(PodConverterCatalog):
    def is_static(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = "No converter was able to answer if this obj is static"
        return self._call_until_success("is_static", (type_,), dict(), error_msg)

    def calc_max_size(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = "No converter was able to calculate maximum size of obj"
        return self._call_until_success("calc_max_size", (type_,), dict(), error_msg)

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

        return helpers


_BYTES_CATALOG = BytesPodConverterCatalog()
_BYTES_CATALOG.register(CustomBytesPodConverter())
