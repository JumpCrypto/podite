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

