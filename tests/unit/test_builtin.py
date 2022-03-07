from typing import Optional, Tuple

from pod import pod, U16, U32, get_catalog


def test_bytes_bool():
    @pod
    class A:
        x: bool
        y: U16

    assert A.is_static()
    assert A.calc_size() == 3

    assert A.from_bytes(b"\x01\x00\x00").x
    assert A.from_bytes(b"\x01\x05\x06").x
    assert not A.from_bytes(b"\x00\x05\x06").x


def test_bytes_str():
    @pod
    class A:
        x: bool
        y: str

    assert not A.is_static()

    assert A.from_bytes(b"\x01\x03\x00\x00\x00\x00\x00\x00\x00abc").x
    assert A.from_bytes(b"\x01\x03\x00\x00\x00\x00\x00\x00\x00abc").y == "abc"


def test_json_bool():
    @pod
    class A:
        x: bool
        y: U16

    assert A.from_dict(dict(x=True, y=5)).x is True
    assert A.from_dict(dict(x=False, y=5)).x is False


def test_bytes_optional():
    type_ = Optional[U32]
    catalog = get_catalog("bytes")

    assert not catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 5

    assert catalog.unpack(type_, b"\x00") is None
    assert catalog.unpack(type_, b"\x01\x05\x00\x00\x00") == 5


def test_json_optional():
    @pod
    class A:
        x: bool
        y: U32

    type_ = Optional[A]
    catalog = get_catalog("json")

    assert catalog.pack(type_, None) is None
    assert catalog.unpack(type_, None) is None

    assert catalog.pack(type_, A(x=True, y=18)) == dict(x=True, y=18)
    assert catalog.unpack(type_, dict(x=True, y=18)) == A(x=True, y=18)


def test_bytes_tuple_static():
    type_ = Tuple[bool, U32]
    catalog = get_catalog("bytes")

    assert catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 5

    assert catalog.unpack(type_, b"\x01\x05\x00\x00\x00") == (True, 5)
    assert catalog.unpack(type_, b"\x00\x00\x06\x00\x00") == (False, 6 * 2 ** 8)


def test_bytes_tuple_static_forward_ref():
    type_ = Tuple[bool, Element, U32]
    catalog = get_catalog("bytes")

    assert catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 7

    assert catalog.unpack(type_, b"\x01\x00\x01\x05\x00\x00\x00") == (
        True,
        Element(False, True),
        5,
    )
    assert catalog.unpack(type_, b"\x00\x01\x00\x00\x06\x00\x00") == (
        False,
        Element(True, False),
        6 * 2 ** 8,
    )


def test_json_tuple_static():
    @pod
    class A:
        x: bool
        y: U32

    type_ = Tuple[A, U32]
    catalog = get_catalog("json")

    assert catalog.pack(type_, (A(x=True, y=9), 18)) == (dict(x=True, y=9), 18)
    assert catalog.unpack(type_, (dict(x=True, y=9), 18)) == (A(x=True, y=9), 18)


def test_bytes_tuple_dynamic():
    type_ = Tuple[bool, Optional[U32]]
    catalog = get_catalog("bytes")

    assert not catalog.is_static(type_)
    assert catalog.calc_max_size(type_) == 6

    assert catalog.unpack(type_, b"\x01\x00") == (True, None)
    assert catalog.unpack(type_, b"\x00\x01\x06\x00\x00\x00") == (False, 6)


def test_json_tuple_dynamic():
    type_ = Tuple[bool, Optional[U32]]
    catalog = get_catalog("json")

    assert catalog.pack(type_, (True, 18)) == (True, 18)
    assert catalog.unpack(type_, (True, 18)) == (True, 18)

    assert catalog.pack(type_, (False, None)) == (False, None)
    assert catalog.unpack(type_, (False, None)) == (False, None)


def test_json_int():
    catalog = get_catalog("json")

    assert catalog.pack(int, 10) == 10
    assert catalog.unpack(int, 10) == 10


def test_json_str():
    catalog = get_catalog("json")

    assert catalog.pack(str, "test") == "test"
    assert catalog.unpack(str, "test") == "test"


def test_json_bytes():
    catalog = get_catalog("json")

    assert catalog.pack(bytes, b"test") == [ord(ch) for ch in "test"]
    assert catalog.unpack(bytes, [ord(ch) for ch in "test"]) == b"test"


@pod
class Element:
    a: bool
    b: bool
