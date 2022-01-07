from enum import _is_sunder, _is_dunder, _is_descriptor  # type: ignore
from dataclasses import dataclass
from typing import Optional, Type

from pod.bytes import _BYTES_CATALOG
from pod.json import _JSON_CATALOG
from pod.decorators import (
    POD_OPTIONS,
    POD_OPTIONS_OVERRIDE,
    POD_OPTIONS_DATACLASS_FN,
)

from .atomic import U8

_VALUES_TO_NAMES = "__enum_values_to_names__"
_NAMES_TO_VARIANTS = "__enum_names_to_variants__"

ENUM_OPTIONS = "__enum_options__"
ENUM_TAG_TYPE = "tag_type"
ENUM_TAG_NAME = "json_tag_name"
ENUM_TAG_VALUE = "json_tag_value"
ENUM_TAG_NAME_MAP = "json_tag_name_map"

ENUM_DEFAULT_TAG_NAME = "name"
ENUM_DEFAULT_TAG_VALUE = None
ENUM_DEFAULT_TAG_NAME_MAP = None


class EnumMeta(type):
    @staticmethod
    def get_member_names(classdict):
        return [
            key
            for key, val in classdict.items()
            if not _is_sunder(key) and not _is_dunder(key) and not _is_descriptor(val)
        ]

    def __new__(mcs, clsname, bases, classdict):
        member_names = mcs.get_member_names(classdict)

        if POD_OPTIONS in member_names:
            member_names.remove(POD_OPTIONS)

        if not member_names:
            return super().__new__(mcs, clsname, bases, classdict)

        for b in bases:
            if hasattr(b, _VALUES_TO_NAMES):
                raise RuntimeError("Enum classes cannot be extended.")

        classdict = dict(classdict)
        prev_value = None
        for name in member_names:
            variant = classdict[name]

            if variant is None or isinstance(variant, int):
                variant = Variant(value=variant)
            else:
                if not isinstance(variant, Variant):
                    raise TypeError(
                        "Enum's variants should be either None, an int, or of type Variant."
                    )

            if variant.name is None:
                variant.name = name

            if variant.prev_value is None:
                variant.prev_value = prev_value

            if variant.value is None:
                variant.assign_value()

            prev_value = variant.value

            if not isinstance(variant.value, int):
                raise TypeError("Variant's value must be either an int or None")

            classdict[name] = variant

        cls = super().__new__(mcs, clsname, bases, classdict)

        values_to_names = {}
        names_to_variants = {}
        for name in member_names:
            variant = classdict[name]
            value = variant.value

            instance = cls(value, None)
            setattr(cls, name, instance)

            if value in values_to_names:
                raise ValueError("Repeated value is not allowed in enums.")

            values_to_names[value] = name
            names_to_variants[name] = variant

        setattr(cls, _VALUES_TO_NAMES, values_to_names)
        setattr(cls, _NAMES_TO_VARIANTS, names_to_variants)

        return cls

    def __getitem__(self, item):
        variant = getattr(self, _NAMES_TO_VARIANTS)[item]
        return self(variant.value)


@dataclass(init=False)
class Variant:
    name: Optional[str] = None
    prev_value: Optional[int] = None
    value: Optional[int] = None
    field: Optional[Type] = None

    def __init__(self, value=None, field=None):
        self.value = value
        self.field = field

    def assign_value(self):
        if self.prev_value is None:
            self.value = 0
        else:
            self.value = self.prev_value + 1

    def to_bytes_partial(self, buffer, obj):
        # Notice that tag value is already serialized
        if self.field is not None:
            _BYTES_CATALOG.pack_partial(self.field, buffer, obj.field)

    def from_bytes_partial(self, buffer, instance):
        # Notice is that tag value is already deserialized
        if self.field is not None:
            field = _BYTES_CATALOG.unpack_partial(self.field, buffer)
            instance = instance(field)

        return instance

    def to_json(self, obj, result):
        # Tag name/value is encoded in result
        if self.field is not None:
            result["field"] = _JSON_CATALOG.pack(self.field, obj.field)

    def from_json(self, instance, raw):
        # Tag name/value is encoded in raw
        if self.field is not None:
            field = _JSON_CATALOG.unpack(self.field, raw["field"])
            return instance(field)
        return instance


class Enum(int, metaclass=EnumMeta):  # type: ignore
    """
    The base class for pod enums.

    Unlike python's Enum class, this class can be instantiated and
    supports enum field.
    """

    field: Optional[Type]

    __pod_options__ = {
        POD_OPTIONS_OVERRIDE: ("to_bytes", "from_bytes"),
        POD_OPTIONS_DATACLASS_FN: None,
    }

    def __new__(cls, value, field=None):
        obj = super().__new__(cls, value)
        super(Enum, obj).__setattr__("field", field)
        return obj

    def __call__(self, field):
        return type(self)(self, field)

    def __repr__(self):
        return "<%s.%s: %r (field=%s)>" % (
            self.__class__.__name__,
            self.get_name(),
            int(self),
            self.field,
        )

    def __str__(self):
        return "%s.%s" % (self.__class__.__name__, self.get_name())

    def __eq__(self, other):
        if int(self) != int(other):
            return False

        if not type(self) == type(other):
            return False

        return self.field == other.field

    def __hash__(self):
        return hash((type(self), int(self), self.field))

    def __setattr__(self, key, value):
        # TODO what is the right exception to raise?
        raise TypeError("Enum objects are immutable")

    @classmethod
    def _is_static(cls) -> bool:
        for variant in getattr(cls, _NAMES_TO_VARIANTS).values():
            if variant.field is not None:
                return False
        return True

    @classmethod
    def _calc_max_size(cls):
        tag_type = cls.get_tag_type()
        val_size = _BYTES_CATALOG.calc_max_size(tag_type)
        max_field_size = 0
        for variant in getattr(cls, _NAMES_TO_VARIANTS).values():
            if variant.field is None:
                variant_size = 0
            else:
                variant_size = _BYTES_CATALOG.calc_max_size(variant.field)

            max_field_size = max(max_field_size, variant_size)

        return val_size + max_field_size

    @classmethod
    def _to_bytes_partial(cls, buffer, obj):
        _BYTES_CATALOG.pack_partial(cls.get_tag_type(), buffer, obj)

        variant: Variant = obj.get_variant()
        variant.to_bytes_partial(buffer, obj)

    @classmethod
    def _from_bytes_partial(cls, buffer):
        tag_type = cls.get_tag_type()
        tag = _BYTES_CATALOG.unpack_partial(tag_type, buffer)

        instance = cls(tag)
        variant = instance.get_variant()
        return variant.from_bytes_partial(buffer, instance)

    @classmethod
    def _transform_name(cls, name):
        mapping = cls._get_json_tag_name_map()
        if mapping is None:
            return name
        elif mapping == "lower":
            mapping = str.lower
        elif mapping == "upper":
            mapping = str.upper
        elif mapping == "capitalize":
            mapping = str.capitalize

        return mapping(name)

    @classmethod
    def _to_json(cls, obj):
        result = {}

        name_key = cls._get_json_tag_name_key()
        if name_key is not None:
            result[name_key] = cls._transform_name(obj.get_variant().name)

        value_key = cls._get_json_tag_value_key()
        if value_key is not None:
            result[value_key] = int(obj)

        variant: Variant = obj.get_variant()
        variant.to_json(obj, result)

        return result

    @classmethod
    def _from_json(cls, raw):
        name_key = cls._get_json_tag_name_key()
        if name_key is not None:
            name = raw[name_key]
            for member_name in cls.get_member_names():
                if cls._transform_name(member_name) == name:
                    instance = cls[member_name]
                    break
            else:
                raise ValueError(f"No member with name {name} was found in this enum.")
        else:
            value_key = cls._get_json_tag_value_key()
            if value_key is not None:
                value = raw[value_key]
                instance = cls(value)
            else:
                raise RuntimeError(
                    "Either name or value should be present for unpacking json"
                )

        variant = instance.get_variant()
        return variant.from_json(instance, raw)

    @classmethod
    def get_options(cls):
        return getattr(cls, ENUM_OPTIONS, {})

    @classmethod
    def get_tag_type(cls):
        return cls.get_options().get(ENUM_TAG_TYPE, U8)

    @classmethod
    def _get_json_tag_name_key(cls):
        return cls.get_options().get(ENUM_TAG_NAME, ENUM_DEFAULT_TAG_NAME)

    @classmethod
    def _get_json_tag_value_key(cls):
        return cls.get_options().get(ENUM_TAG_VALUE, ENUM_DEFAULT_TAG_VALUE)

    @classmethod
    def _get_json_tag_name_map(cls):
        return cls.get_options().get(
            ENUM_TAG_NAME_MAP, ENUM_DEFAULT_TAG_NAME_MAP
        )

    def get_variant(self) -> Variant:
        return getattr(type(self), _NAMES_TO_VARIANTS)[self.get_name()]

    @classmethod
    def get_member_names(cls):
        return tuple(getattr(cls, _VALUES_TO_NAMES).values())

    def get_name(self):
        return getattr(type(self), _VALUES_TO_NAMES)[int(self)]
