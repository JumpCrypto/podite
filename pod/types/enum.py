import enum
from dataclasses import dataclass
from typing import Optional, Type

from pod.bytes import _BYTES_CATALOG
from pod.types.atomic import U8
from pod.decorators import (
    _POD_OPTIONS,
    _POD_OPTIONS_OVERRIDE,
    _POD_OPTIONS_DATACLASS_FN,
)

_VALUES_TO_NAMES = "__enum_values_to_names__"
_NAMES_TO_VARIANTS = "__enum_names_to_variants__"

_SAME_LEN_VARIANTS = "__enum_same_len_variants__"
_ENUM_VALUE_TYPE = "__enum_value_type__"


class EnumMeta(type):
    @classmethod
    def __prepare__(metacls, cls, bases):
        return enum._EnumDict()  # type: ignore

    def __new__(mcs, clsname, bases, classdict):
        member_names = classdict._member_names
        if _POD_OPTIONS in member_names:
            member_names.remove(_POD_OPTIONS)

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
        return getattr(self, _NAMES_TO_VARIANTS)[item]


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


class Enum(int, metaclass=EnumMeta):  # type: ignore
    """
    The base class for pod enums.

    Unlike python's Enum class, this class can be instantiated and
    supports enum field.
    """

    field: Optional[Type]

    __pod_options__ = {
        _POD_OPTIONS_OVERRIDE: ("to_bytes", "from_bytes"),
        _POD_OPTIONS_DATACLASS_FN: None,
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

    def get_variant(self):
        return getattr(type(self), _NAMES_TO_VARIANTS)[self.get_name()]

    def get_field_type(self):
        return self.get_variant().field

    @classmethod
    def get_val_type(cls):
        return getattr(cls, _ENUM_VALUE_TYPE, U8)

    @classmethod
    def _is_static(cls) -> bool:
        if getattr(cls, _SAME_LEN_VARIANTS, False):
            return True

        for variant in getattr(cls, _NAMES_TO_VARIANTS).values():
            if variant.field is not None:
                return False
        return True

    @classmethod
    def _calc_max_size(cls):
        val_type = cls.get_val_type()
        val_size = _BYTES_CATALOG.calc_max_size(val_type)
        max_field_size = 0
        for variant in getattr(cls, _NAMES_TO_VARIANTS).values():
            if variant.field is None:
                variant_size = 0
            else:
                print(variant.field)
                variant_size = _BYTES_CATALOG.calc_max_size(variant.field)

            max_field_size = max(max_field_size, variant_size)

        return val_size + max_field_size

    @classmethod
    def _to_bytes_partial(cls, buffer, obj):
        val_type = cls.get_val_type()
        _BYTES_CATALOG.pack_partial(val_type, buffer, obj)

        field_type = obj.get_field_type()
        if field_type is not None:
            _BYTES_CATALOG.pack_partial(field_type, buffer, obj.field)

    @classmethod
    def _from_bytes_partial(cls, buffer):
        val_type = cls.get_val_type()
        value = _BYTES_CATALOG.unpack_partial(val_type, buffer)

        instance = cls(value)
        field_type = instance.get_field_type()
        if field_type is not None:
            field = _BYTES_CATALOG.unpack_partial(field_type, buffer)
            instance = instance(field)

        return instance

    def get_name(self):
        return getattr(type(self), _VALUES_TO_NAMES)[int(self)]
