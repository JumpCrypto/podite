from dataclasses import dataclass
from enum import _is_sunder, _is_dunder, _is_descriptor  # type: ignore
from io import BytesIO
from typing import (
    Optional,
    Type,
    NamedTuple,
    Tuple,
    Dict,
    Generic,
    TypeVar,
    get_args,
    get_origin,
)

from podite.bytes import BYTES_CATALOG
from podite.core import POD_SELF_CONVERTER
from podite.decorators import (
    POD_OPTIONS,
    POD_OPTIONS_OVERRIDE,
    POD_OPTIONS_DATACLASS_FN,
)
from podite.json import JSON_CATALOG
from .atomic import U8
from .misc import static_from_bytes_partial, static_to_bytes_partial
from .. import pod
from .._utils import (
    resolve_name_mapping,
    get_calling_module,
    get_concrete_type,
    FORMAT_BORSH,
    FORMAT_ZERO_COPY,
    AutoTagTypeValueManager,
    FORMAT_TO_TYPE,
)

_VALUES_TO_NAMES = "__enum_values_to_names__"
_NAMES_TO_VARIANTS = "__enum_names_to_variants__"

ENUM_OPTIONS = "__enum_options__"
ENUM_TAG_NAME = "json_tag_name"
ENUM_TAG_NAME_MAP = "json_tag_name_map"

ENUM_DEFAULT_TAG_NAME = None
ENUM_DEFAULT_TAG_NAME_MAP = None


class EnumMeta(type(Generic)):  # type: ignore
    @staticmethod
    def get_member_names(classdict):
        return [
            key
            for key, val in classdict.items()
            if not _is_sunder(key) and not _is_dunder(key) and not _is_descriptor(val)
        ]

    def __new__(mcs, clsname, bases, classdict):
        cls = super().__new__(mcs, clsname, bases, classdict)

        member_names = mcs.get_member_names(classdict)
        if not member_names:
            return cls

        if POD_OPTIONS in member_names:
            member_names.remove(POD_OPTIONS)

        for b in bases:
            if hasattr(b, _VALUES_TO_NAMES):
                raise RuntimeError("Enum classes cannot be extended.")

        prev_value = None
        variants = dict()
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

            if variant.value is None:
                variant.assign_value(cls, prev_value)

            prev_value = variant.value

            if not isinstance(variant.value, int):
                raise TypeError("Variant's value must be either an int or None")

            variants[name] = variant

        values_to_names = {}
        for name, variant in variants.items():
            value = variant.value

            instance = cls(value, None)
            setattr(cls, name, instance)

            if value in values_to_names:
                raise ValueError("Repeated value is not allowed in enums.")

            values_to_names[value] = name

        setattr(cls, _VALUES_TO_NAMES, values_to_names)
        setattr(cls, _NAMES_TO_VARIANTS, variants)

        return cls

    def __getitem__(self, item):
        if self == Enum:
            return self.__class_getitem__(item)

        variant = getattr(self, _NAMES_TO_VARIANTS)[item]
        return self(variant.value)


@dataclass(init=False)
class Variant:
    name: Optional[str] = None
    value: Optional[int] = None
    field: Optional[Type] = None
    module: Optional[Tuple[Dict, Dict]] = None

    def __init__(self, value=None, field=None, module=None):
        self.value = value
        self.field = field
        if module is None:
            self.module = get_calling_module()
        else:
            self.module = module

    @property
    def concrete_field_type(self):
        if isinstance(self.field, str):
            return get_concrete_type(self.module, self.field)
        return self.field

    def assign_value(self, _cls, prev_value):
        if prev_value is None:
            self.value = 0
        else:
            self.value = prev_value + 1

    def to_bytes_partial(self, buffer, obj, **kwargs):
        # Notice that tag value is already serialized
        if self.field is not None:
            BYTES_CATALOG.pack_partial(
                self.concrete_field_type, buffer, obj.field, **kwargs
            )

    def from_bytes_partial(self, buffer, instance, **kwargs):
        # Notice that tag value is already deserialized
        if self.field is not None:
            field = BYTES_CATALOG.unpack_partial(
                self.concrete_field_type, buffer, **kwargs
            )
            instance = instance(field)

        return instance

    def to_dict(self, obj):
        if self.field is None:
            return None

        return JSON_CATALOG.pack(self.concrete_field_type, obj.field)

    def from_dict(self, instance, raw):
        # Tag name/value is encoded in raw
        if self.field is not None:
            field = JSON_CATALOG.unpack(self.concrete_field_type, raw)
            return instance(field)
        return instance


TagType = TypeVar("TagType")


class Enum(int, Generic[TagType], metaclass=EnumMeta):  # type: ignore
    """
    The base class for podite enums.

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
        if self.field is None:
            return "%s.%s" % (
                self.__class__.__name__,
                self.get_name(),
            )

        return "%s.%s(field=%s)" % (
            self.__class__.__name__,
            self.get_name(),
            repr(self.field),
        )

    def __str__(self):
        return "<%s.%s: %r (field=%s)>" % (
            self.__class__.__name__,
            self.get_name(),
            int(self),
            self.field,
        )

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        return self.is_a(other) and self.field == other.field

    def is_a(self, variant):
        """
        Usage: `val.is_a(Option.Some)
        """
        return type(self) == type(variant) and int(self) == int(variant)

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
    def _calc_size(cls, obj, format=FORMAT_BORSH, **kwargs):
        tag_type = cls.get_tag_type()
        val_size = BYTES_CATALOG.calc_size(tag_type, **kwargs)
        max_field_size = 0
        variant: Variant = cls._get_variant(obj.get_name())
        if variant.field is not None:
            return val_size + BYTES_CATALOG.calc_size(
                variant.concrete_field_type, obj.field
            )
        return val_size

    @classmethod
    def _calc_max_size(cls):
        tag_type = cls.get_tag_type()
        val_size = BYTES_CATALOG.calc_max_size(tag_type)
        max_field_size = 0
        for variant in getattr(cls, _NAMES_TO_VARIANTS).values():
            if variant.field is None:
                variant_size = 0
            else:
                variant_size = BYTES_CATALOG.calc_max_size(variant.concrete_field_type)
            max_field_size = max(max_field_size, variant_size)

        return val_size + max_field_size

    @classmethod
    def _to_bytes_partial(cls, buffer, instance, format=FORMAT_BORSH, **kwargs):
        if format == FORMAT_ZERO_COPY:
            static_to_bytes_partial(
                cls._inner_to_bytes_partial,
                cls,
                buffer,
                instance,
                format=format,
                **kwargs,
            )
            return
        cls._inner_to_bytes_partial(buffer, instance, format=format, **kwargs)

    @classmethod
    def _from_bytes_partial(cls, buffer, format=FORMAT_BORSH, **kwargs):
        if format == FORMAT_ZERO_COPY:
            return static_from_bytes_partial(
                cls._inner_from_bytes_partial, cls, buffer, format=format, **kwargs
            )
        return cls._inner_from_bytes_partial(buffer, format=format, **kwargs)

    @classmethod
    def _inner_to_bytes_partial(cls, buffer, instance, **kwargs):
        BYTES_CATALOG.pack_partial(cls.get_tag_type(), buffer, instance, **kwargs)

        variant: Variant = cls._get_variant(instance.get_name())
        variant.to_bytes_partial(buffer, instance, **kwargs)

    @classmethod
    def _inner_from_bytes_partial(cls, buffer, **kwargs):
        tag_type = cls.get_tag_type()
        tag = BYTES_CATALOG.unpack_partial(tag_type, buffer, **kwargs)

        instance = cls(tag)
        variant = cls._get_variant(instance.get_name())
        return variant.from_bytes_partial(buffer, instance, **kwargs)

    @classmethod
    def _transform_name(cls, name):
        mapping = cls._get_json_tag_name_map()
        mapping = resolve_name_mapping(mapping)

        return mapping(name)

    @classmethod
    def _inv_transform_name(cls, name):
        for member_name in cls.get_member_names():
            if cls._transform_name(member_name) == name:
                return member_name

        raise ValueError(f"No member with name {name} was found in this enum.")

    @classmethod
    def _to_dict(cls, instance):
        variant: Variant = cls._get_variant(instance.get_name())
        field_json = variant.to_dict(instance)

        name_key = cls._get_json_tag_name_key()
        name_val = cls._transform_name(instance.get_name())
        if name_key is None:
            if variant.field is None:
                return name_val

            return {name_val: field_json}
        else:
            if field_json is None:
                field_json = {}

            if not isinstance(field_json, dict):
                raise ValueError(
                    "When tag name is specified, the field's return value should be a dict."
                )
            field_json[name_key] = name_val
            return field_json

    @classmethod
    def _from_dict(cls, raw):
        name_key = cls._get_json_tag_name_key()
        if name_key is None:

            if isinstance(raw, str):
                transformed_name = raw
                field_json = None
            elif isinstance(raw, dict) and len(raw) == 1:
                transformed_name = list(raw)[0]
                field_json = raw[transformed_name]
            else:
                raise ValueError(
                    "When tag is not specified, input should be either a str or a dict of len 1."
                )
        elif isinstance(raw, dict) and name_key in raw:
            transformed_name = raw[name_key]
            field_json = dict(**raw)
            del field_json[name_key]
            if not field_json:
                field_json = None
        else:
            raise ValueError(
                "Unknown input."
            )  # TODO do a better error handling in this case

        member_name = cls._inv_transform_name(transformed_name)
        instance = cls[member_name]
        variant = cls._get_variant(instance.get_name())
        return variant.from_dict(instance, field_json)

    @classmethod
    def get_options(cls):
        return getattr(cls, ENUM_OPTIONS, {})

    @classmethod
    def get_tag_type(cls):
        orig_bases = getattr(cls, "__orig_bases__")

        # when Enum[...] is a superclass of cls
        for base in orig_bases:
            if get_origin(base) == Enum:
                return get_args(base)[0]

        # return the default tag type
        return U8

    @classmethod
    def _get_json_tag_name_key(cls):
        return cls.get_options().get(ENUM_TAG_NAME, ENUM_DEFAULT_TAG_NAME)

    @classmethod
    def _get_json_tag_name_map(cls):
        return cls.get_options().get(ENUM_TAG_NAME_MAP, ENUM_DEFAULT_TAG_NAME_MAP)

    @classmethod
    def _get_variant(cls, name) -> Variant:
        return getattr(cls, _NAMES_TO_VARIANTS)[name]

    @classmethod
    def get_member_names(cls):
        return tuple(getattr(cls, _VALUES_TO_NAMES).values())

    def get_name(self):
        return getattr(type(self), _VALUES_TO_NAMES)[int(self)]


def named_fields(**kwargs):
    cls = pod(NamedTuple("Pod", kwargs.items()), dataclass_fn=dataclass(init=False))  # type: ignore

    # making sure that it works when tuples are passed too
    def safe_cast(obj):
        if isinstance(obj, (tuple, list)):
            return cls(*obj)
        if isinstance(obj, dict):
            return cls(**obj)
        return obj

    to_bytes = cls._to_bytes_partial
    cls._to_bytes_partial = lambda buffer, obj, format=FORMAT_BORSH: to_bytes(
        buffer, safe_cast(obj), format=format
    )

    to_dict = cls._to_dict
    cls._to_dict = lambda obj: to_dict(cls(*obj))

    return cls


@dataclass(init=False)
class AutoTagType:
    @classmethod
    def _is_static(cls) -> bool:
        return False

    @classmethod
    def _calc_size(cls, obj, **kwargs):
        return BYTES_CATALOG.calc_size(AutoTagTypeValueManager.get_tag())

    @classmethod
    def _calc_max_size(cls):
        return BYTES_CATALOG.calc_max_size(AutoTagTypeValueManager.get_tag())

    @classmethod
    def _to_bytes_partial(cls, buffer, obj, **kwargs):
        BYTES_CATALOG.pack_partial(
            AutoTagTypeValueManager.get_tag(), buffer, obj, **kwargs
        )

    @classmethod
    def _from_bytes_partial(cls, buffer: BytesIO, **kwargs):
        return BYTES_CATALOG.unpack_partial(
            AutoTagTypeValueManager.get_tag(), buffer, **kwargs
        )

    @classmethod
    def _to_dict(cls, obj):
        return obj

    @classmethod
    def _from_dict(cls, obj):
        return obj


# register that AutoTagType knows how to convert itself to bytes
setattr(AutoTagType, POD_SELF_CONVERTER, ["bytes"])
