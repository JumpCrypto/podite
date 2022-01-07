from pod import (
    FixedLenArray,
    FixedLenBytes,
    FixedLenStr,
    Vec,
    Str,
    Bytes,
    U16,
    U32,
)


def test_fixed_len_array():
    type_ = FixedLenArray[U32, 10]

    assert type_.is_static()
    assert type_.calc_max_size() == 40

    actual = type_.from_bytes(b"\x01\x00\x00\x00" * 10)
    expect = [1] * 10

    assert actual == expect


def test_fixed_len_bytes():
    type_ = FixedLenBytes[10]

    assert type_.is_static()
    assert type_.calc_max_size() == 10

    actual = type_.from_bytes(bytes(range(10)))
    expect = bytes(range(10))

    assert actual == expect


def test_fixed_len_str():
    type_ = FixedLenStr[10]

    assert type_.is_static()
    assert type_.calc_max_size() == 10

    actual = type_.from_bytes(bytes(range(1, 6)).ljust(10, b"\x00"))
    expect = bytes(range(1, 6)).decode("utf-8")

    assert actual == expect


def test_vec():
    type_ = Vec[U16, 10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 24  # 4 + 2 * 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i, 0])

    actual = type_.from_bytes(raw)
    expect = [2 * i for i in range(5)]

    assert actual == expect


def test_bytes():
    type_ = Bytes[10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 14  # 4 + 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i])

    actual = type_.from_bytes(raw)
    expect = bytes([2 * i for i in range(5)])

    assert actual == expect


def test_str():
    type_ = Str[10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 14  # 4 + 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i])

    actual = type_.from_bytes(raw)
    expect = bytes([2 * i for i in range(5)]).decode("utf-8")

    assert actual == expect
