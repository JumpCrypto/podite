from pod.decorators import pod
from pod.json import POD_OPTIONS_RENAME
from pod.types.atomic import I8, I16, U8, I32, U128


def test_bytes_simple():
    @pod
    class A:
        x: I16
        y: I32
        z: U128

    assert A.is_static()
    assert A.calc_max_size() == 22  # = 4(x) + 2(y) + 16(z)

    a1 = A(x=5, y=18, z=12)
    pa = A.to_bytes(a1)
    assert len(pa) == A.calc_size()

    a2 = A.from_bytes(pa)
    assert a1 == a2


def test_json_simple():
    @pod
    class A:
        x: I16
        y: I32
        z: U128

    a = A(x=5, y=18, z=12)
    assert A.to_dict(a) == dict(x=5, y=18, z=12)
    assert a == A.from_dict(dict(x=5, y=18, z=12))


def test_bytes_inheritance():
    @pod
    class A:
        x: I8
        ay: U8

    @pod
    class B(A):
        x: I32
        by: U128

    assert B.is_static()
    assert B.calc_max_size() == 21  # = 4(x) + 1(ay) + 16(by)

    b1 = B(x=5, ay=18, by=12)
    pb = B.to_bytes(b1)
    assert len(pb) == B.calc_size()

    b2 = B.from_bytes(pb)
    assert b1 == b2


def test_json_inheritance():
    @pod
    class A:
        x: I8
        ay: U8

    @pod
    class B(A):
        x: I32
        by: U128

    b1 = B(x=5, ay=18, by=12)

    assert B.to_dict(b1) == dict(x=5, ay=18, by=12)
    assert b1 == B.from_dict(dict(x=5, ay=18, by=12))


def test_json_name_fields():
    @pod
    class A:
        __pod_options__ = {POD_OPTIONS_RENAME: "upper"}
        x: I8
        y: U8

    a = A(x=5, y=18)

    assert A.to_dict(a) == dict(X=5, Y=18)
    assert a == A.from_dict(dict(X=5, Y=18))
