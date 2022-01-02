from io import BytesIO
from abc import ABC, abstractmethod
from typing import Tuple

from .core import PodConverter


class BytesPodConverter(PodConverter, ABC):
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
            remaining = buffer.getvalue()
            if len(remaining) > 0:
                raise RuntimeError("Unused bytes in provided raw data")

        return success, obj

    @abstractmethod
    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        raise NotImplementedError


TO_BYTES_PARTIAL = "_to_bytes_partial"
FROM_BYTES_PARTIAL = "_from_bytes_partial"


class CustomBytesPodConverter(BytesPodConverter):
    def pack_partial(self, type_, buffer, obj, **kwargs) -> bool:
        if not hasattr(type_, TO_BYTES_PARTIAL):
            return False

        method = getattr(type_, TO_BYTES_PARTIAL)
        method(type_, buffer, obj, **kwargs)
        return True

    def unpack_partial(self, type_, buffer, **kwargs) -> Tuple[bool, object]:
        if not hasattr(type_, FROM_BYTES_PARTIAL):
            return False, None

        method = getattr(type_, FROM_BYTES_PARTIAL)
        return True, method(type_, buffer, **kwargs)
