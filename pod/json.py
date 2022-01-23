import json

from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields
from typing import Dict, Callable, Any

from ._utils import resolve_name_mapping
from .core import PodConverterCatalog, POD_SELF_CONVERTER

TO_JSON = "_to_json"
FROM_JSON = "_from_json"

MISSING = object()

POD_OPTIONS_RENAME = "rename"


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
        def to_json_file(cls, filename, obj, /, mode="w", **kwargs):
            with open(filename, mode) as fin:
                obj = cls.to_json(obj, **kwargs)
                print(obj, file=fin)

        @classmethod  # type: ignore[misc]
        def from_json(cls, raw, **kwargs):
            return cls.unpack(raw, converter="json", **kwargs)

        @classmethod  # type: ignore[misc]
        def from_json_file(cls, filename, /, **kwargs):
            with open(filename, "r") as fin:
                raw = json.load(fin)
                return cls.from_json(raw, **kwargs)

        helpers["to_json"] = to_json
        helpers["to_json_file"] = to_json_file

        helpers["from_json"] = from_json
        helpers["from_json_file"] = from_json_file

        if is_dataclass(type_):
            helpers.update(self._generate_packers(type_))

        return helpers

    def _generate_packers(self, type_) -> Dict[str, Callable]:
        helpers: Dict[str, Callable] = {}

        from .decorators import POD_OPTIONS

        options = getattr(type_, POD_OPTIONS, {})
        rename_fn = options.get(POD_OPTIONS_RENAME, lambda x: x)
        rename_fn = resolve_name_mapping(rename_fn)

        @classmethod  # type: ignore[misc]
        def _to_json(cls, obj):
            values = {}
            for field in fields(cls):
                value = getattr(obj, field.name)
                values[rename_fn(field.name)] = self.pack(
                    cls._get_field_type(field.type), value
                )

            return values

        @classmethod  # type: ignore[misc]
        def _from_json(cls, obj, **kwargs):
            values = {}
            for field in fields(cls):
                field_value = obj.get(rename_fn(field.name), MISSING)
                if field_value is not MISSING:
                    values[field.name] = self.unpack(
                        cls._get_field_type(field.type), field_value
                    )
            return cls(**values)

        helpers[TO_JSON] = _to_json
        helpers[FROM_JSON] = _from_json

        return helpers


_JSON_CATALOG = JsonPodConverterCatalog()
_JSON_CATALOG.register(SelfJsonPodConverter().get_mapping)
