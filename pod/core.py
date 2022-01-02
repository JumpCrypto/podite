# encoding: utf-8
"""
Core functionality and base classes of pod packing/unpacking are implemented here.
"""
from abc import abstractmethod, ABC
from typing import Dict, List, Tuple
from collections import defaultdict


class PodConverter(ABC):
    """
    The base class for all POD converters.
    """

    @abstractmethod
    def pack(self, type_, obj, **kwargs) -> Tuple[bool, object]:
        """
        Packs obj according to given type_.

        :param type_: the *template* type used for packing
        :param obj: the actual object to be packed
        :param kwargs: keyword arguments to be passed to converters
        :return: A bool indicating success and the packed object (None if unsuccessful)
        """
        raise NotImplementedError

    @abstractmethod
    def unpack(self, type_, raw, checked=False, **kwargs):
        """
        Unpacks raw according to given type_.

        :param type_: the *template* type used for packing
        :param raw: the actual object to be packed
        :param checked: if true, an exception will be raised if raw is not fully consumed
        :param kwargs: keyword arguments to be passed to converters
        :return: A bool indicating success and the unpacked object (None if unsuccessful)
        """
        raise NotImplementedError


class PodConverterCatalog:
    """
    The class to hold a list of possible converters to apply when packing/unpacking until a
    success happens.
    """

    converters: List[PodConverter]

    def __init__(self):
        self.converters = []

    def register(self, converter: PodConverter):
        """
        Registers a new converter to be used if previous converters fail to pack/unpack.
        """
        assert isinstance(converter, PodConverter)
        self.converters.append(converter)

    def pack(self, type_, obj, **kwargs):
        """
        Packs obj according to given type_ by trying all registered converters.
        """
        for converter in self.converters:
            success, result = converter.pack(type_, obj, **kwargs)
            if success:
                return result

        raise ValueError("No converter was able to pack object")

    def unpack(self, type_, raw, checked=False, **kwargs):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        for converter in self.converters:
            success, result = converter.unpack(type_, raw, checked=checked, **kwargs)
            if success:
                return result

        raise ValueError("No converter was able to unpack raw data")


_CATALOGS: Dict[str, PodConverterCatalog] = defaultdict(PodConverterCatalog)


def get_catalog(name):
    """
    Returns a converter catalog corresponding to name (e.g., for name="bytes" or name="json").
    """
    return _CATALOGS[name]
