from pod import pod, U16, U32, Option, Static, Enum, Variant, Default


def test_bytes_static_option():
    option = Option[U32]
    type_ = Static[option]

    assert type_.is_static()
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
    assert type_.calc_max_size() == 3

    actual = type_.from_bytes(b"\x00\x00\x00")
    expect = option.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00")
    expect = option.SOME(5)

    assert actual == expect


@pod
class Element:
    a: U16


def test_bytes_static_enum():
    @pod
    class A(Enum):
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
    class A(Enum):
        X = Variant(3)
        Y = Variant(field=U32)
        Z = Variant(8, field=U16)

    type_ = Static[A]

    assert type_.to_json(A.X) == "X"
    assert type_.from_json("X") == A.X

    assert type_.to_json(A.Y) == {"Y": None}
    assert type_.from_json("Y") == A.Y

    assert type_.to_json(A.Z(10)) == {"Z": 10}
    assert type_.from_json({"Z": 10}) == A.Z(10)


def test_json_default():
    @pod
    class A:
        x: int
        y: Default[list[int], lambda: [18]]

    assert A.to_json(A(5, [7])) == dict(x=5, y=[7])
    assert A(5, [7]) == A.from_json(dict(x=5, y=[7]))
    assert A(5, [18]) == A.from_json(dict(x=5))


@pod
class Container:
    x: U32
    y: "Contained"


@pod
class Contained:
    z: int


def test_json_forward_ref():
    raw = dict(x=5, y=dict(z=6))

    actual = Container.from_json(raw)
    expect = Container(5, Contained(6))

    assert actual == expect
