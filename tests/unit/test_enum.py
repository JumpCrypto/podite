from pod.decorators import pod
from pod.types.atomic import U16, U32
from pod.types.enum import Enum, Variant, ENUM_TAG_NAME_MAP, ENUM_TAG_NAME


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

    assert A.to_json(A.Y) == "Y"
    assert A.to_json(A.Z) == "Z"


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


def test_json_enum_with_field():
    @pod
    class A(Enum):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    assert A.to_json(A.X) == "X"
    assert A.to_json(A.Y(5)) == {"Y": 5}
    assert A.to_json(A.Z(7)) == {"Z": 7}

    assert A.X == A.from_json("X")
    assert A.Y(5) == A.from_json({"Y": 5})
    assert A.Z(7) == A.from_json({"Z": 7})


def test_json_enum_name_mapping():
    @pod
    class A(Enum):
        __enum_options__ = {
            ENUM_TAG_NAME_MAP: "lower"
        }
        X = None
        Y = None
        Z = None

    assert A.to_json(A.Y) == "y"
    assert A.to_json(A.Z) == "z"

    assert A.Y == A.from_json("y")
    assert A.Z == A.from_json("z")


def test_json_enum_tagged():
    @pod
    class A(Enum):
        __enum_options__ = {
            ENUM_TAG_NAME: "kind"
        }
        X = None
        Y = None
        Z = None #Variant(field=U32)

    assert A.to_json(A.Y) == dict(kind="Y")
    assert A.to_json(A.Z) == dict(kind="Z")
    # assert A.to_json(A.Z(5)) == dict(kind="z", field=5)

    assert A.Y == A.from_json(dict(kind="Y"))
    assert A.Z == A.from_json(dict(kind="Z"))
    # assert A.Z(5) == A.from_json(dict(name="z", field=5))
