import enum

from typing import Union, List, Iterable, Container, Callable, Dict
from dataclasses import dataclass

from pod import get_catalog


def _process_class(
    type_,
    converters: Iterable[str] = ("bytes",),
    override: Union[bool, Container[str]] = False,
    dataclass_fn="auto",
):
    if dataclass_fn == "auto":
        if issubclass(type_, enum.Enum):
            dataclass_fn = None
        else:
            dataclass_fn = dataclass

    if dataclass_fn:
        type_ = dataclass_fn(type_)

    @classmethod  # type: ignore[misc]
    def pack(cls, obj, converter, **kwargs):
        return get_catalog(converter).pack(cls, obj, **kwargs)

    @classmethod  # type: ignore[misc]
    def unpack(cls, raw, converter, **kwargs):
        print(get_catalog(converter))
        return get_catalog(converter).unpack(cls, raw, **kwargs)

    helpers: Dict[str, Callable] = {
        "pack": pack,
        "unpack": unpack,
    }

    for c in converters:
        helpers.update(get_catalog(c).generate_helpers(type_))

    for name, method in helpers.items():
        should_bind = True
        if hasattr(type_, name):
            if not override:
                should_bind = False
            else:
                if isinstance(override, Container):
                    should_bind = name in override

        if should_bind:
            setattr(type_, name, method)

    return type_


def pod(
    cls=None,
    /,
    converters=("bytes",),
    override: Union[bool, List[str]] = False,
    dataclass_fn="auto",
):
    def wrap(cls_):
        return _process_class(cls_, converters, override, dataclass_fn)

    if cls is None:
        return wrap

    return wrap(cls)
