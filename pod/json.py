from dataclasses import is_dataclass, fields
from io import BytesIO
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Callable, Any

from .core import PodConverterCatalog, POD_SELF_CONVERTER

TO_JSON = "_to_json"
FROM_JSON = "_from_json"

MISSING = object()


class JsonPodConverter(ABC):
    @abstractmethod
    def pack_obj(self, type_, obj, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        raise NotImplementedError


class SelfJsonPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        converters = getattr(type_, POD_SELF_CONVERTER, ())
        if "json" in converters:
            return self
        return None

    def pack_obj(self, type_, obj, **kwargs) -> Any:
        return getattr(type_, TO_JSON)(obj, **kwargs)

    def unpack_obj(self, type_, obj, **kwargs) -> Any:
        return getattr(type_, FROM_JSON)(obj, **kwargs)


class JsonPodConverterCatalog(PodConverterCatalog[JsonPodConverter]):
    def pack(self, type_, obj, **kwargs):
        error_msg = "No converter was able to pack raw data"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.pack_obj(type_, obj, **kwargs)

    def unpack(self, type_, raw, **kwargs) -> object:
        error_msg = "No converter was able to unpack object"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.unpack_obj(type_, raw, **kwargs)

    def generate_helpers(self, type_) -> Dict[str, Callable]:
        helpers = super().generate_helpers(type_)

        @classmethod  # type: ignore[misc]
        def to_json(cls, obj, **kwargs):
            return cls.pack(obj, converter="json", **kwargs)

        @classmethod  # type: ignore[misc]
        def from_json(cls, raw, **kwargs):
            return cls.unpack(raw, converter="json", **kwargs)

        helpers["to_json"] = to_json
        helpers["from_json"] = from_json

        if is_dataclass(type_):
            helpers.update(self._generate_packers())

        return helpers

    def _generate_packers(self) -> Dict[str, Callable]:
        helpers: Dict[str, Callable] = {}

        @classmethod  # type: ignore[misc]
        def _to_json(cls, obj):
            values = {}
            for field in fields(cls):
                value = getattr(obj, field.name)
                values[field.name] = self.pack(field.type, value)

            return values

        @classmethod  # type: ignore[misc]
        def _from_json(cls, obj, **kwargs):
            values = {}
            for field in fields(cls):
                field_value = obj.get(field.name, MISSING)
                values[field.name] = self.unpack(field.type, field_value)
            return cls(**values)

        helpers[TO_JSON] = _to_json
        helpers[FROM_JSON] = _from_json

        return helpers


_JSON_CATALOG = JsonPodConverterCatalog()
_JSON_CATALOG.register(SelfJsonPodConverter().get_mapping)
