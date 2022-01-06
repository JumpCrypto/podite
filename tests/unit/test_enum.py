from pod.decorators import pod
from pod.types.atomic import U16, U32
from pod.types.enum import Enum, Variant


def test_enum_without_field():
    @pod
    class A(Enum):
        X = None
        Y = None
        Z = None

    assert A.is_static()
    assert A.calc_max_size() == 1

    assert A.to_bytes(A.Y) == b"\x01"
    assert A.from_bytes(b"\x02") == A.Z


def test_enum_with_field():
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
