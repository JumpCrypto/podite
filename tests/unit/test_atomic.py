from pod import Bool, I8, U8, I32l, I32b, U32b, I128l, I128b, U128l, U128b


def test_bytes_bool():
    assert Bool.is_static()
    assert Bool.calc_size() == 1

    assert Bool.from_bytes(b"\x01")
    assert not Bool.from_bytes(b"\x00")


def test_json_bool():
    assert Bool.to_json(True)
    assert not Bool.to_json(False)

    assert Bool.from_json(True)
    assert not Bool.from_json(False)


def test_bytes_i8():
    assert I8.is_static()
    assert I8.calc_size() == 1

    assert I8.from_bytes(b"a", checked=True) == ord("a")
    assert I8.from_bytes(bytes([200])) == -56
    assert I8.from_bytes(b"ab") == ord("a")


def test_json_i8():
    assert I8.to_json(8) == 8
    assert I8.from_json(8) == 8


def test_bytes_u8():
    assert U8.is_static()
    assert U8.calc_size() == 1

    assert U8.from_bytes(b"a", checked=True) == ord("a")
    assert U8.from_bytes(bytes([200])) == 200
    assert U8.from_bytes(b"ab") == ord("a")


def test_json_u8():
    assert U8.to_json(8) == 8
    assert U8.from_json(8) == 8


def test_bytes_i32l():
    assert I32l.is_static()
    assert I32l.calc_size() == 4

    assert I32l.from_bytes(bytes([200, 0, 0, 0])) == 200
    assert I32l.from_bytes(bytes([200, 0, 0, 210])) == (200 + 210 * 2 ** 24) - (2 ** 32)


def test_json_i32l():
    assert I32l.to_json(123456) == 123456
    assert I32l.from_json(123456) == 123456


def test_bytes_i32b():
    assert I32b.is_static()
    assert I32b.calc_size() == 4

    assert I32b.from_bytes(bytes([200, 0, 0, 0])) == 200 * 2 ** 24 - 2 ** 32
    assert I32b.from_bytes(bytes([0, 0, 0, 210])) == 210


def test_json_i32b():
    assert I32b.to_json(123456) == 123456
    assert I32b.from_json(123456) == 123456


def test_bytes_u32b():
    assert U32b.is_static()
    assert U32b.calc_size() == 4

    assert U32b.from_bytes(bytes([200, 0, 0, 0])) == 200 * 2 ** 24
    assert U32b.from_bytes(bytes([200, 0, 0, 210])) == (210 + 200 * 2 ** 24)


def test_bytes_i128l():
    assert I128l.is_static()
    assert I128l.calc_size() == 16

    assert I128l.from_bytes(b"\x80".ljust(16, b"\x00")) == 128
    assert I128l.from_bytes(b"\x80".rjust(16, b"\x00")) == 2 ** 127 - 2 ** 128


def test_bytes_u128l():
    assert U128l.is_static()
    assert U128l.calc_size() == 16

    assert U128l.from_bytes(b"\x80".ljust(16, b"\x00")) == 128
    assert U128l.from_bytes(b"\x80".rjust(16, b"\x00")) == 2 ** 127


def test_bytes_i128b():
    assert I128b.is_static()
    assert I128b.calc_size() == 16

    assert I128b.from_bytes(b"\x80".rjust(16, b"\x00")) == 128
    assert I128b.from_bytes(b"\x80".ljust(16, b"\x00")) == 2 ** 127 - 2 ** 128


def test_bytes_u128b():
    assert U128b.is_static()
    assert U128b.calc_size() == 16

    assert U128b.from_bytes(b"\x80".rjust(16, b"\x00")) == 128
    assert U128b.from_bytes(b"\x80".ljust(16, b"\x00")) == 2 ** 127


def test_json_u128l():
    assert I128l.to_json(12345678910) == 12345678910
    assert I128l.from_json(12345678910) == 12345678910
