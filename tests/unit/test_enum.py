from pod.decorators import pod
from pod.types.atomic import U16, U32
from pod.types.enum import Enum, Variant


def test_enum_without_field():
    @pod
    class A(Enum):
        x = None
        y = None
        z = None

    assert A.is_static()
    assert A.calc_max_size() == 1

    assert A.to_bytes(A.y) == b"\x01"
    assert A.from_bytes(b"\x02") == A.z


def test_enum_with_field():
    @pod
    class A(Enum):
        x = Variant(3)
        y = Variant(field=U32)
        z = Variant(8, field=U16)

    assert not A.is_static()
    assert A.calc_max_size() == 5

    assert A.to_bytes(A.x) == b"\x03"
    assert A.to_bytes(A.y(5)) == b"\x04\x05\x00\x00\x00"
    assert A.to_bytes(A.z(7)) == b"\x08\x07\x00"

    assert A.x == A.from_bytes(b"\x03")
    assert A.y(5) == A.from_bytes(b"\x04\x05\x00\x00\x00")
    assert A.z(7) == A.from_bytes(b"\x08\x07\x00")
