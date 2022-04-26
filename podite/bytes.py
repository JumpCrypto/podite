from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields, dataclass
from io import BytesIO
from typing import Tuple, Dict, Any, Literal
from .errors import PodPathError
from .core import PodConverterCatalog, POD_SELF_CONVERTER
from ._utils import (
    FORMAT_BORSH,
    FORMAT_PASS,
    FORMAT_AUTO,
    FORMAT_ZERO_COPY,
    FORMAT_TO_TYPE,
    AutoTagTypeValueManager,
)


class BytesPodConverter(ABC):
    @abstractmethod
    def is_static(self, type_) -> bool:
        raise NotImplementedError

    @abstractmethod
    def calc_size(self, type_, obj, **kwargs) -> int:
        """
        Returns the current size of the type. This is equal to the max size when no variable length types are present
        Note: set AutoTagType value using AutoTagTypeValueManager for the format you want the size for
        """
        raise NotImplementedError

    @abstractmethod
    def calc_max_size(self, type_) -> int:
        """
        Returns the maximum size of the type.
        Note: set AutoTagType value using AutoTagTypeValueManager for the format you want the size for
        """
        raise NotImplementedError

    @abstractmethod
    def pack_partial(self, type_, buffer, obj, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def unpack_partial(self, type_, buffer, **kwargs) -> Any:
        raise NotImplementedError


IS_STATIC = "_is_static"
CALC_SIZE = "_calc_size"
CALC_MAX_SIZE = "_calc_max_size"
TO_BYTES_PARTIAL = "_to_bytes_partial"
FROM_BYTES_PARTIAL = "_from_bytes_partial"


def dataclass_is_static(cls) -> bool:
    for field in fields(cls):
        if not BYTES_CATALOG.is_static(cls._get_field_type(field.type)):
            return False
    return True


def dataclass_calc_size(cls, obj):
    total = 0
    for field in fields(cls):
        total += BYTES_CATALOG.calc_size(
            cls._get_field_type(field.type), getattr(obj, field.name)
        )

    return total


def dataclass_calc_max_size(cls):
    total = 0
    for field in fields(cls):
        total += BYTES_CATALOG.calc_max_size(cls._get_field_type(field.type))

    return total


def dataclass_to_bytes_partial(cls, buffer, obj, **kwargs):
    for field in fields(cls):
        value = None
        try:
            value = getattr(obj, field.name)
            BYTES_CATALOG.pack_partial(
                cls._get_field_type(field.type), buffer, value, **kwargs
            )
        except PodPathError as e:
            e.path.append(field.name)
            e.path.append(cls.__name__)
            raise
        except Exception as e:
            raise PodPathError(
                "Failed to serialize dataclass",
                [field.name, cls.__name__],
                field.type.__name__,
                value,
            ) from e


def dataclass_from_bytes_partial(cls, buffer, **kwargs):
    values = {}
    for field in fields(cls):
        try:
            values[field.name] = BYTES_CATALOG.unpack_partial(
                cls._get_field_type(field.type), buffer, **kwargs
            )
        except PodPathError as e:
            e.path.append(field.name)
            e.path.append(cls.__name__)
            raise
        except Exception as e:
            raise PodPathError(
                "Failed to deserialize dataclass",
                [field.name, cls.__name__],
                field.type.__name__,
            ) from e
    return cls(**values)


class SelfBytesPodConverter(BytesPodConverter):
    def get_mapping(self, type_):
        converters = getattr(type_, POD_SELF_CONVERTER, ())
        if "bytes" in converters:
            return self
        return None

    def is_static(self, type_) -> bool:
        return getattr(type_, IS_STATIC)()

    def calc_size(self, type_, obj, **kwargs) -> int:
        return getattr(type_, CALC_SIZE)(obj, **kwargs)

    def calc_max_size(self, type_) -> int:
        return getattr(type_, CALC_MAX_SIZE)()

    def pack_partial(self, type_, buffer, obj, **kwargs) -> Any:
        return getattr(type_, TO_BYTES_PARTIAL)(buffer, obj, **kwargs)

    def unpack_partial(self, type_, buffer, **kwargs) -> Any:
        return getattr(type_, FROM_BYTES_PARTIAL)(buffer, **kwargs)


class BytesPodConverterCatalog(PodConverterCatalog[BytesPodConverter]):
    def is_static(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = "No converter was able to answer if this obj is static"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.is_static(type_)

    def calc_max_size(self, type_):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        error_msg = f"No converter was able to calculate maximum size of type {type_}"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.calc_max_size(type_)

    def calc_size(self, type_, obj=None, format=FORMAT_BORSH, **kwargs):
        # zero-copy format does not support dynamic sizes
        if obj is None or format == FORMAT_ZERO_COPY:
            return self.calc_max_size(type_)

        error_msg = f"No converter was able to calculate size of type {type_}"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.calc_size(type_, obj, **kwargs)

    def pack(self, type_, obj, format=FORMAT_BORSH, **kwargs):
        buffer = BytesIO()
        error_msg = "No converter was able to pack raw data"
        converter = self._get_converter_or_raise(type_, error_msg)

        if format in FORMAT_TO_TYPE:
            with AutoTagTypeValueManager(FORMAT_TO_TYPE[format]):
                self.pack_partial(type_, buffer, obj, format=format, **kwargs)
        elif format == FORMAT_PASS:
            self.pack_partial(type_, buffer, obj, format=format, **kwargs)
        else:
            raise ValueError(
                f"Format argument must be {FORMAT_AUTO}, {FORMAT_BORSH}, or {FORMAT_ZERO_COPY}, found {format}"
            )

        return buffer.getvalue()

    def pack_partial(self, type_, buffer, obj, format=FORMAT_BORSH, **kwargs):
        error_msg = "No converter was able to pack raw data"
        converter = self._get_converter_or_raise(type_, error_msg)

        return converter.pack_partial(type_, buffer, obj, format=format, **kwargs)

    def unpack(self, type_, raw, checked=False, format=FORMAT_AUTO, **kwargs) -> object:
        if not isinstance(raw, BytesIO):
            buffer = BytesIO(raw)
        else:
            buffer = raw

        error_msg = "No converter was able to unpack object"
        converter = self._get_converter_or_raise(type_, error_msg)
        if format == FORMAT_AUTO:
            with AutoTagTypeValueManager(FORMAT_TO_TYPE[FORMAT_ZERO_COPY]):
                pos = buffer.tell()
                buffer.seek(0, 2)
                if converter.calc_max_size(type_) == buffer.tell():
                    format = FORMAT_ZERO_COPY
                else:
                    format = FORMAT_BORSH
                buffer.seek(pos)

        if format in FORMAT_TO_TYPE:
            with AutoTagTypeValueManager(FORMAT_TO_TYPE[format]):
                obj = self.unpack_partial(type_, buffer, format=format, **kwargs)
        elif format == FORMAT_PASS:
            obj = converter.unpack_partial(type_, buffer, format=format, **kwargs)
        else:
            raise ValueError(
                f"Format argument must be {FORMAT_AUTO}, {FORMAT_BORSH}, or {FORMAT_ZERO_COPY}, found {format}"
            )

        if checked and buffer.tell() < len(buffer.getvalue()):
            raise RuntimeError("Unused bytes in provided raw data")

        return obj

    def unpack_partial(
        self, type_, buffer, format=FORMAT_AUTO, **kwargs
    ) -> Tuple[bool, object]:
        error_msg = "No converter was able to unpack object"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.unpack_partial(type_, buffer, format=format, **kwargs)

    def generate_helpers(self, type_) -> Dict[str, classmethod]:
        helpers = super().generate_helpers(type_)

        def is_static(cls):
            return BYTES_CATALOG.is_static(cls)

        def calc_max_size(cls):
            return BYTES_CATALOG.calc_max_size(cls)

        def calc_size(cls, obj=None, format=FORMAT_BORSH, **kwargs):
            if obj is None or format == FORMAT_ZERO_COPY:
                if not cls.is_static():
                    raise RuntimeError(
                        "calc_size can only be called for static classes"
                    )
                return cls.calc_max_size()
            if format == FORMAT_BORSH:
                with AutoTagTypeValueManager(FORMAT_TO_TYPE[FORMAT_BORSH]):
                    return BYTES_CATALOG.calc_size(cls, obj, format=format, **kwargs)
            return BYTES_CATALOG.calc_size(cls, obj, format=format, **kwargs)

        def to_bytes(cls, obj, **kwargs):
            return cls.pack(obj, converter="bytes", **kwargs)

        def from_bytes(cls, raw, format=FORMAT_AUTO, **kwargs):
            return cls.unpack(raw, converter="bytes", format=format, **kwargs)

        helpers.update(
            {
                "is_static": classmethod(is_static),
                "calc_max_size": classmethod(calc_max_size),
                "calc_size": classmethod(calc_size),
                "to_bytes": classmethod(to_bytes),
                "from_bytes": classmethod(from_bytes),
            }
        )

        if is_dataclass(type_):
            helpers.update(self._generate_packers())

        return helpers

    @staticmethod
    def _generate_packers() -> Dict[str, classmethod]:
        return {
            IS_STATIC: classmethod(dataclass_is_static),
            CALC_MAX_SIZE: classmethod(dataclass_calc_max_size),
            CALC_SIZE: classmethod(dataclass_calc_size),
            TO_BYTES_PARTIAL: classmethod(dataclass_to_bytes_partial),
            FROM_BYTES_PARTIAL: classmethod(dataclass_from_bytes_partial),
        }


BYTES_CATALOG = BytesPodConverterCatalog()
BYTES_CATALOG.register(SelfBytesPodConverter().get_mapping)
