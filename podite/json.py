import json

from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields, MISSING
from typing import Dict, Callable, Any

from ._utils import resolve_name_mapping
from .core import PodConverterCatalog, POD_SELF_CONVERTER

TO_DICT = "_to_dict"
FROM_DICT = "_from_dict"

POD_OPTIONS_RENAME = "rename"


class JsonPodConverter(ABC):
    @abstractmethod
    def pack_dict(self, type_, obj, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        raise NotImplementedError


class SelfJsonPodConverter(JsonPodConverter):
    def get_mapping(self, type_):
        converters = getattr(type_, POD_SELF_CONVERTER, ())
        if "json" in converters:
            return self
        return None

    def pack_dict(self, type_, obj, **kwargs) -> Any:
        return getattr(type_, TO_DICT)(obj, **kwargs)

    def unpack_dict(self, type_, obj, **kwargs) -> Any:
        return getattr(type_, FROM_DICT)(obj, **kwargs)


class JsonPodConverterCatalog(PodConverterCatalog[JsonPodConverter]):
    def pack(self, type_, obj, **kwargs):
        error_msg = "No converter was able to pack raw data"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.pack_dict(type_, obj, **kwargs)

    def unpack(self, type_, raw, **kwargs) -> object:
        error_msg = "No converter was able to unpack object"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.unpack_dict(type_, raw, **kwargs)

    def generate_helpers(self, type_) -> Dict[str, classmethod]:
        helpers = super().generate_helpers(type_)

        def to_dict(cls, obj, **kwargs):
            return cls.pack(obj, converter="json", **kwargs)

        def to_dict_file(cls, filename, obj, /, mode="w", **kwargs):
            with open(filename, mode) as fin:
                obj = cls.to_dict(obj, **kwargs)
                print(obj, file=fin)

        def from_dict(cls, raw, **kwargs):
            return cls.unpack(raw, converter="json", **kwargs)

        def from_dict_file(cls, filename, /, **kwargs):
            with open(filename, "r") as fin:
                raw = json.load(fin)
                return cls.from_dict(raw, **kwargs)

        helpers["to_dict"] = classmethod(to_dict)
        helpers["to_dict_file"] = classmethod(to_dict_file)

        helpers["from_dict"] = classmethod(from_dict)
        helpers["from_dict_file"] = classmethod(from_dict_file)

        if is_dataclass(type_):
            helpers.update(self._generate_packers(type_))

        return helpers

    def _generate_packers(self, type_) -> Dict[str, classmethod]:
        from .decorators import POD_OPTIONS

        options = getattr(type_, POD_OPTIONS, {})
        rename_fn = options.get(POD_OPTIONS_RENAME, lambda x: x)
        rename_fn = resolve_name_mapping(rename_fn)

        def _to_dict(cls, obj):
            values = {}
            for field in fields(cls):
                value = getattr(obj, field.name)
                values[rename_fn(field.name)] = self.pack(
                    cls._get_field_type(field.type), value
                )

            return values

        def _from_dict(cls, obj, **kwargs):
            values = {}
            for field in fields(cls):
                field_value = obj.get(rename_fn(field.name), MISSING)
                has_default = (
                    field.default is not MISSING or field.default_factory is not MISSING
                )
                if field_value is not MISSING or not has_default:
                    values[field.name] = self.unpack(
                        cls._get_field_type(field.type), field_value
                    )
            return cls(**values)

        return {
            TO_DICT: classmethod(_to_dict),
            FROM_DICT: classmethod(_from_dict),
        }


JSON_CATALOG = JsonPodConverterCatalog()
JSON_CATALOG.register(SelfJsonPodConverter().get_mapping)
