from pod import U32, Option, Static, Enum, Variant, U16, pod


def test_static_option():
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


def test_static_enum():
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
