import enum
import functools

from typing import Union, Iterable, Container, Callable, Dict, Literal
from dataclasses import dataclass, field as _field

from podite import get_catalog
from podite.core import POD_SELF_CONVERTER

POD_OPTIONS = "__pod_options__"
POD_OPTIONS_OVERRIDE = "override"
POD_OPTIONS_DATACLASS_FN = "dataclass_fn"


def _process_class(
    type_,
    converters: Iterable[str],
    override: Union[bool, Container[str], Literal["auto"]],
    dataclass_fn,
):
    pod_config = getattr(type_, POD_OPTIONS, {})
    if dataclass_fn == "auto":
        if issubclass(type_, enum.Enum):
            dataclass_fn = None
        else:
            dataclass_fn = pod_config.get(POD_OPTIONS_DATACLASS_FN, dataclass)

    if dataclass_fn:
        type_ = dataclass_fn(type_)

    if override == "auto":
        override = pod_config.get(POD_OPTIONS_OVERRIDE, False)

    setattr(type_, POD_SELF_CONVERTER, converters)

    @classmethod  # type: ignore[misc]
    def pack(cls, obj, converter, **kwargs):
        return get_catalog(converter).pack(cls, obj, **kwargs)

    @classmethod  # type: ignore[misc]
    def unpack(cls, raw, converter, **kwargs):
        return get_catalog(converter).unpack(cls, raw, **kwargs)

    methods: Dict[str, Callable] = {
        "pack": pack,
        "unpack": unpack,
    }

    for catalog in map(get_catalog, converters):
        methods.update(catalog.generate_helpers(type_))

    for name, method in methods.items():
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
    converters=("bytes", "json"),
    override: Union[bool, Container[str], Literal["auto"]] = "auto",
    dataclass_fn="auto",
):
    """
    podite is the decorator used to annotate classes whose fields are also podite types
    """

    def wrap(cls_):
        return _process_class(cls_, converters, override, dataclass_fn)

    if cls is None:
        return wrap

    return wrap(cls)


pod_json = functools.partial(pod, converters=("json",))
pod_bytes = functools.partial(pod, converters=("bytes",))

# for future flexibility
field = _field
