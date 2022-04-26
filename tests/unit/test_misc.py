from podite import (
    pod,
    U16,
    U32,
    Option,
    Static,
    Enum,
    Variant,
    Default,
    field,
    U8,
    AutoTagTypeValueManager,
)


def test_bytes_static_option():
    option = Option[U32]
    type_ = Static[option]

    assert type_.is_static()
    assert type_.calc_max_size() == 12

    with AutoTagTypeValueManager(U8):
        assert type_.calc_max_size() == 5

    actual = type_.from_bytes(b"\x00\x00\x00\x00\x00")
    expect = option.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00\x00\x00")
    expect = option.SOME(5)

    assert actual == expect


def test_bytes_static_option_forward_ref():
    option = Option["Element"]
    type_ = Static[option]

    assert type_.is_static()
    assert type_.calc_max_size() == 10
    with AutoTagTypeValueManager(U8):
        assert type_.calc_max_size() == 3

    actual = type_.from_bytes(b"\x00\x00\x00")
    expect = option.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00")
    expect = option.SOME(Element(5))

    assert actual == expect


@pod
class Element:
    a: U16


def test_bytes_static_enum():
    @pod
    class A(Enum[U8]):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    type_ = Static[A]

    assert type_.is_static()
    assert type_.calc_max_size() == 5

    assert type_.to_bytes(A.X) == b"\x03".ljust(5, b"\x00")
    assert type_.to_bytes(A.Y(5)) == b"\x04\x05\x00\x00\x00".ljust(5, b"\x00")
    assert type_.to_bytes(A.Z(7)) == b"\x08\x07\x00".ljust(5, b"\x00")

    assert A.X == type_.from_bytes(b"\x03".ljust(5, b"\x00"))
    assert A.Y(5) == type_.from_bytes(b"\x04\x05\x00\x00\x00".ljust(5, b"\x00"))
    assert A.Z(7) == type_.from_bytes(b"\x08\x07\x00".ljust(5, b"\x00"))


def test_json_static_enum():
    @pod
    class A(Enum[U8]):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    type_ = Static[A]

    assert type_.to_dict(A.X) == "X"
    assert type_.from_dict("X") == A.X

    assert type_.to_dict(A.Y) == {"Y": None}
    assert type_.from_dict("Y") == A.Y

    assert type_.to_dict(A.Z(10)) == {"Z": 10}
    assert type_.from_dict({"Z": 10}) == A.Z(10)


def test_json_field():
    @pod
    class A:
        x: int
        y: list[int] = field(default_factory=lambda: [18])

    assert A.to_dict(A(5, [7])) == dict(x=5, y=[7])
    assert A(5, [7]) == A.from_dict(dict(x=5, y=[7]))
    assert A(5, [18]) == A.from_dict(dict(x=5))


def test_json_default():
    @pod
    class A:
        x: Default[int, lambda: 18]
        y: int
        z: list[int] = field(default_factory=lambda: [12])

    assert A.to_dict(A(x=10, y=5)) == dict(x=10, y=5, z=[12])
    assert A(18, 9, [12]) == A.from_dict(dict(y=9))


@pod
class Container:
    x: U32
    y: "Contained"


@pod
class Contained:
    z: int


def test_json_forward_ref():
    raw = dict(x=5, y=dict(z=6))

    actual = Container.from_dict(raw)
    expect = Container(5, Contained(6))

    assert actual == expect
