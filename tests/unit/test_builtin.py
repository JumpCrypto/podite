from typing import Optional, Tuple

from pod import pod, U16, U32, get_catalog


def test_bool():
    @pod
    class A:
        x: bool
        y: U16

    assert A.is_static()
    assert A.calc_size() == 3

    assert A.from_bytes(b"\x01\x00\x00").x
    assert A.from_bytes(b"\x01\x05\x06").x
    assert not A.from_bytes(b"\x00\x05\x06").x


def test_optional():
    type_ = Optional[U32]
    catalog = get_catalog("bytes")

    assert not catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 5

    assert catalog.unpack(type_, b"\x00") is None
    assert catalog.unpack(type_, b"\x01\x05\x00\x00\x00") == 5


def test_tuple_static():
    type_ = Tuple[bool, U32]
    catalog = get_catalog("bytes")

    assert catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 5

    assert catalog.unpack(type_, b"\x01\x05\x00\x00\x00") == (True, 5)
    assert catalog.unpack(type_, b"\x00\x00\x06\x00\x00") == (False, 6 * 2 ** 8)


def test_tuple_dynamic():
    type_ = Tuple[bool, Optional[U32]]
    catalog = get_catalog("bytes")

    assert not catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 6

    assert catalog.unpack(type_, b"\x01\x00") == (True, None)
    assert catalog.unpack(type_, b"\x00\x01\x06\x00\x00\x00") == (False, 6)
