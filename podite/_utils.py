import inspect
from functools import lru_cache, partial

FORMAT_AUTO = "FORMAT_AUTO"  # attempt to determine format
FORMAT_PASS = "FORMAT_PASS"  # rely on previously set AutoTagTypeValue
FORMAT_ZERO_COPY = "FORMAT_ZERO_COPY"  # use rust's in-memory format
FORMAT_BORSH = "FORMAT_BORSH"  # use borsh format

# don't import U8 and U64 to avoid cycles
FORMAT_TO_TYPE = {FORMAT_BORSH: "U8", FORMAT_ZERO_COPY: "U64"}  # stub  # stub


class AutoTagTypeValueManager:
    TAG_TYPE = [None]  # mutable static var

    @staticmethod
    def get_tag():
        return AutoTagTypeValueManager.TAG_TYPE[0]

    def __init__(self, tag_type_or_format):
        if isinstance(tag_type_or_format, str):
            tag_type_or_format = FORMAT_TO_TYPE[tag_type_or_format]
        self._tag_type = tag_type_or_format

    def __enter__(self):
        self.old = AutoTagTypeValueManager.TAG_TYPE[0]
        AutoTagTypeValueManager.TAG_TYPE[0] = self._tag_type

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old is not None:
            AutoTagTypeValueManager.TAG_TYPE[0] = self.old


class _GetitemToCall:
    def __init__(self, name, func):
        self.name = name
        self.func = lru_cache()(partial(func, name))

    def __getitem__(self, args):
        if isinstance(args, tuple):
            return self.func(*args)
        else:
            return self.func(args)

    def __str__(self):
        return f"{_GetitemToCall.__module__}.{self.name}"

    def __repr__(self):
        return str(self)


def resolve_name_mapping(mapping):
    if mapping is None:
        return lambda x: x
    elif mapping == "lower":
        mapping = str.lower
    elif mapping == "upper":
        mapping = str.upper
    elif mapping == "capitalize":
        mapping = str.capitalize
    return mapping


def get_calling_module(level=3):
    frame = inspect.stack()[level]
    return inspect.getmodule(frame[0])


def get_concrete_type(module, type_):
    if isinstance(type_, str):
        module_dict = {name: getattr(module, name) for name in dir(module)}
        return eval(type_, module_dict, dict())
    return type_
