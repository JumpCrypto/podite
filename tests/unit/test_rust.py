from pod.types.atomic import U32
from pod.types.rust import Option


def test_option_packed():
    type_ = Option[U32]

    assert not type_.is_static()
    assert type_.calc_max_size() == 5

    actual = type_.from_bytes(b"\x00")
    expect = type_.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00\x00\x00")
    expect = type_.SOME(5)

    assert actual == expect


def test_option_not_packed():
    type_ = Option[U32, False]

    assert type_.is_static()
    assert type_.calc_max_size() == 5

    actual = type_.from_bytes(b"\x00\x00\x00\x00\x00")
    expect = type_.NONE

    assert actual == expect

    actual = type_.from_bytes(b"\x01\x05\x00\x00\x00")
    expect = type_.SOME(5)

    assert actual == expect
