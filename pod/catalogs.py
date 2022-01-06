from typing import Dict

from . import PodConverterCatalog
from .bytes import _BYTES_CATALOG

_CATALOGS: Dict[str, PodConverterCatalog] = {
    "bytes": _BYTES_CATALOG,
}


def get_catalog(name):
    """
    Returns a converter catalog corresponding to name (e.g., for name="bytes" or name="json").
    """
    return _CATALOGS[name]
