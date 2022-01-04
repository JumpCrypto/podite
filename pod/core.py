# encoding: utf-8
"""
Core functionality and base classes of pod packing/unpacking are implemented here.
"""
from abc import abstractmethod, ABC
from typing import List, Tuple, Union, Dict, Callable


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

    def _call_until_success(self, name, args, kwargs, error_msg):
        for converter in self.converters:
            method = getattr(converter, name)
            success, result = method(*args, **kwargs)
            if success:
                return result
        raise ValueError(error_msg)

    def pack(self, type_, obj, **kwargs):
        """
        Packs obj according to given type_ by trying all registered converters.
        """
        args = type_, obj
        error_msg = "No converter was able to pack object"
        return self._call_until_success("pack", args, kwargs, error_msg)

    def unpack(self, type_, raw, **kwargs):
        """
        Unpacks obj according to given type_ by trying all registered converters.
        """
        args = type_, raw
        error_msg = "No converter was able to unpack raw data"
        return self._call_until_success("unpack", args, kwargs, error_msg)

    def generate_helpers(self, type_) -> Dict[str, Callable]:
        return dict()
