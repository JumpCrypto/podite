from pod import (
    FixedLenArray,
    FixedLenBytes,
    FixedLenStr,
    Vec,
    Str,
    Bytes,
    U16,
    U32,
    pod,
    Bool,
)


def test_bytes_fixed_len_array():
    type_ = FixedLenArray[U32, 10]

    assert type_.is_static()
    assert type_.calc_max_size() == 40

    actual = type_.from_bytes(b"\x01\x00\x00\x00" * 10)
    expect = [1] * 10

    assert actual == expect


def test_json_fixed_len_array():
    type1 = FixedLenArray[U32, 10]

    actual = type1.from_json([1] * 10)
    expect = [1] * 10

    assert actual == expect

    @pod
    class A:
        x: Bool
        y: U32

    type2 = FixedLenArray[A, 10]

    actual = type2.from_json([dict(x=bool(i % 2), y=i) for i in range(10)])
    expect = [A(bool(i % 2), i) for i in range(10)]

    print(actual)
    assert actual == expect


def test_bytes_fixed_len_bytes():
    type_ = FixedLenBytes[10]

    assert type_.is_static()
    assert type_.calc_max_size() == 10

    actual = type_.from_bytes(bytes(range(10)))
    expect = bytes(range(10))

    assert actual == expect


def test_json_fixed_len_bytes():
    type_ = FixedLenBytes[10]

    assert type_.from_json(list(range(10))) == bytes(range(10))
    assert list(range(10)) == type_.to_json(bytes(range(10)))


def test_bytes_fixed_len_str():
    type_ = FixedLenStr[10]

    assert type_.is_static()
    assert type_.calc_max_size() == 10

    actual = type_.from_bytes(bytes(range(1, 6)).ljust(10, b"\x00"))
    expect = bytes(range(1, 6)).decode("utf-8")

    assert actual == expect


def test_json_fixed_len_str():
    type_ = FixedLenStr[10]

    assert type_.from_json("test") == "test"
    assert type_.to_json("test") == "test"


def test_bytes_vec():
    type_ = Vec[U16, 10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 24  # 4 + 2 * 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i, 0])

    actual = type_.from_bytes(raw)
    expect = [2 * i for i in range(5)]

    assert actual == expect


def test_bytes_bytes():
    type_ = Bytes[10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 14  # 4 + 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i])

    actual = type_.from_bytes(raw)
    expect = bytes([2 * i for i in range(5)])

    assert actual == expect


def test_bytes_str():
    type_ = Str[10]

    assert not type_.is_static()
    assert type_.calc_max_size() == 14  # 4 + 10

    raw = bytes([5, 0, 0, 0])
    for i in range(5):
        raw += bytes([2 * i])

    actual = type_.from_bytes(raw)
    expect = bytes([2 * i for i in range(5)]).decode("utf-8")

    assert actual == expect
