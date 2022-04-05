# encoding: utf-8
"""
Core functionality and base classes of podite packing/unpacking are implemented here.
"""
import sys
from typing import List, Dict, Callable, TypeVar, Generic, Type, Optional

PodConverter = TypeVar("PodConverter")

POD_SELF_CONVERTER = "__pod_self_converter__"
GET_FIELD_TYPE = "_get_field_type"


class PodConverterCatalog(Generic[PodConverter]):
    """
    The class to hold a list of possible converters to apply when packing/unpacking until a
    success happens.
    """

    converters: List[Callable[[Type], Optional[PodConverter]]]

    def __init__(self):
        self.converters = []

    def register(self, converter: Callable[[Type], Optional[PodConverter]]):
        """
        Registers a new converter to be used if previous converters fail to pack/unpack.
        """
        self.converters.append(converter)

    def _get_converter_or_raise(self, type_, msg):
        for mapping in self.converters:
            converter = mapping(type_)
            if converter:
                return converter

        raise ValueError(msg)

    def _call_until_success(self, name, args, kwargs, error_msg):
        for converter in self.converters:
            method = getattr(converter, name)
            success, result = method(*args, **kwargs)
            if success:
                return result
        raise ValueError(error_msg)

    def pack(self, type_, obj, **kwargs):
        """
        Packs obj according to given type_.

        :param type_: the *template* type used for packing
        :param obj: the actual object to be packed
        :param kwargs: keyword arguments to be passed to converters
        :return: A bool indicating success and the packed object (None if unsuccessful)
        """
        error_msg = "No converter was able to pack object"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.pack(type_, obj, **kwargs)

    def unpack(self, type_, raw, **kwargs):
        """
        Unpacks raw according to given type_.

        :param type_: the *template* type used for packing
        :param raw: the actual object to be packed
        :param checked: if true, an exception will be raised if raw is not fully consumed
        :param kwargs: keyword arguments to be passed to converters
        :return: A bool indicating success and the unpacked object (None if unsuccessful)
        """
        error_msg = "No converter was able to unpack raw data"
        converter = self._get_converter_or_raise(type_, error_msg)
        return converter.unpack(type_, raw, **kwargs)

    def generate_helpers(self, type_) -> Dict[str, classmethod]:
        def _get_field_type(cls, field):
            if isinstance(field, str):
                module = sys.modules[cls.__module__]
                return getattr(module, field)
            else:
                return field

        return {GET_FIELD_TYPE: classmethod(_get_field_type)}
