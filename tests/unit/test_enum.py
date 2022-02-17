import functools
from typing import Optional

from pod.decorators import pod
from pod.types.atomic import U16, U32, U8
from pod.types.enum import Enum, Variant, ENUM_TAG_NAME_MAP, ENUM_TAG_NAME, named_fields


def test_bytes_enum_without_field():
    @pod
    class A(Enum):
        X = None
        Y = None
        Z = None

    assert A.is_static()
    assert A.calc_max_size() == 1

    assert A.to_bytes(A.Y) == b"\x01"
    assert A.from_bytes(b"\x02") == A.Z


def test_json_enum_without_field():
    @pod
    class A(Enum):
        X = None
        Y = None
        Z = None

    assert A.to_dict(A.Y) == "Y"
    assert A.to_dict(A.Z) == "Z"


def test_bytes_enum_with_field():
    @pod
    class A(Enum):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    assert not A.is_static()
    assert A.calc_max_size() == 5

    assert A.to_bytes(A.X) == b"\x03"
    assert A.to_bytes(A.Y(5)) == b"\x04\x05\x00\x00\x00"
    assert A.to_bytes(A.Z(7)) == b"\x08\x07\x00"

    assert A.X == A.from_bytes(b"\x03")
    assert A.Y(5) == A.from_bytes(b"\x04\x05\x00\x00\x00")
    assert A.Z(7) == A.from_bytes(b"\x08\x07\x00")


def test_bytes_enum_with_tag_type():
    @pod
    class A(Enum[U16]):
        X = Variant(3)
        Y = Variant()
        Z = Variant(8, field=U16)

    # import pdb
    # pdb.set_trace()

    assert not A.is_static()
    assert A.calc_max_size() == 4

    assert A.to_bytes(A.X) == b"\x03\x00"
    assert A.to_bytes(A.Y) == b"\x04\x00"
    assert A.to_bytes(A.Z(7)) == b"\x08\x00\x07\x00"

    assert A.X == A.from_bytes(b"\x03\x00")
    assert A.Y == A.from_bytes(b"\x04\x00")
    assert A.Z(7) == A.from_bytes(b"\x08\x00\x07\x00")


def test_json_enum_with_field():
    @pod
    class A(Enum):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    assert A.to_dict(A.X) == "X"
    assert A.to_dict(A.Y(5)) == {"Y": 5}
    assert A.to_dict(A.Z(7)) == {"Z": 7}

    assert A.X == A.from_dict("X")
    assert A.Y(5) == A.from_dict({"Y": 5})
    assert A.Z(7) == A.from_dict({"Z": 7})


def test_json_enum_name_mapping():
    @pod
    class A(Enum):
        __enum_options__ = {ENUM_TAG_NAME_MAP: "lower"}
        X = None
        Y = None
        Z = None

    assert A.to_dict(A.Y) == "y"
    assert A.to_dict(A.Z) == "z"

    assert A.Y == A.from_dict("y")
    assert A.Z == A.from_dict("z")


def test_json_enum_tagged():
    t = named_fields(b=int, c=str)

    @pod
    class B(Enum):
        __enum_options__ = {ENUM_TAG_NAME: "kind"}
        X = None
        Y = None
        Z = Variant(field=Optional[t])

    assert B.to_dict(B.Y) == dict(kind="Y")
    assert B.to_dict(B.Z) == dict(kind="Z")
    assert B.to_dict(B.Z((5, 6))) == dict(kind="Z", b=5, c=6)

    assert B.Y == B.from_dict(dict(kind="Y"))
    assert B.Z == B.from_dict(dict(kind="Z"))
    assert B.Z(t(b=5, c=6)) == B.from_dict(dict(kind="Z", b=5, c=6))


def test_enum_instances_eq():
    @functools.lru_cache
    def get_class():
        @pod
        class A(Enum):
            APPLE = None
            INT = Variant(field=U8)
        return A
    A1 = get_class()
    A2 = get_class()

    assert A1.APPLE == A2.APPLE
    assert A1.INT(1) == A1.INT(1)
