from typing import Dict

from . import PodConverterCatalog


def get_catalog(name):
    """
    Returns a converter catalog corresponding to name (e.g., for name="bytes" or name="json").
    """
    return _CATALOGS[name]


from .bytes import BYTES_CATALOG
from .json import JSON_CATALOG


_CATALOGS: Dict[str, PodConverterCatalog] = {
    "bytes": BYTES_CATALOG,
    "json": JSON_CATALOG,
}
