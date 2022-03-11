from pod import U8, U32, Option, AutoTagTypeValueManager


def test_option_packed():
    type_ = Option[U32]

    assert not type_.is_static()
    assert type_.calc_max_size() == 12
    with AutoTagTypeValueManager(U8):
        assert type_.calc_max_size() == 5

    actual = type_.from_bytes(b"\x00")
    expect = type_.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00\x00\x00")
    expect = type_.SOME(5)

    assert actual == expect


def test_option_equal():
    a = Option[U32]
    b = Option[U32]
    c = Option[U8]

    assert a == b
    assert type(a) == type(b)

    assert a.NONE == b.NONE
    assert a.SOME(2) == b.SOME(2)

    x = a.SOME(2)
    y = b.SOME(3)
    eq = x == y
    assert not eq
    assert x != y

    assert b.NONE != c.NONE
    assert b.SOME(1) != c.SOME(1)
    assert b.SOME(2) != c.SOME(1)
