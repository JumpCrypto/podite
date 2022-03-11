from pod import (
    FixedLenArray,
    FixedLenStr,
    Option,
    Vec,
    Str,
    Bytes,
    U64,
    U16,
    pod,
    U8,
    PodPathError,
)


@pod
class Simple:
    a: U64
    b: U16
    padding: FixedLenStr[6]


@pod
class MyStruct:
    a_builtin: U8
    a_string: Str[10]
    a_array: FixedLenArray[U8, 10]
    a_bytes: Bytes[512]
    a_vec: Vec[Option[Str[10]], 10]
    simple_vec: Vec[Simple, 10]


def test_write_to_files_for_rust_deserialization():
    serialized = Simple.to_bytes(Simple(5, 125, "ByeBye"))
    with open("tests/round_trip_rust/simple.bytes", "wb") as f:
        f.write(serialized)


def test_round_trip_bytes():
    O = Option[Str[10]]

    simple = Simple(5, 123, "PodStr")
    assert Simple.calc_size(simple) == 8 + 2 + 6
    assert Bytes[512].calc_size(bytes([1, 2, 3])) == 4 + 3
    val = MyStruct(
        8,
        "hi",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        bytes([1, 2, 3]),
        [
            Option[Str[10]].SOME("hi"),
            Option[Str[10]].NONE,
            O.SOME("bye"),
            O.SOME("sad"),
        ],
        [Simple(5, 124, "PodStr")]
    )

    # sizes
    a_builtin = 1
    a_string = 4 + 2
    a_array = 10
    a_bytes = 4 + 3
    a_vec = (4 + (1 + 4 + 2) + 1 + 2 * (1 + 4 + 3))
    simple_vec = (4 + 1 * (8 + 2 + 6))
    assert MyStruct.calc_size(obj=val) == a_builtin + a_string + a_array + a_bytes + a_vec + simple_vec

    serialized = MyStruct.to_bytes(val)
    deserialized = MyStruct.from_bytes(serialized)

    assert val == deserialized


def test_fixed_len_array_wrong_size():
    @pod
    class AnArray:
        b: FixedLenArray[U8, 10]

    @pod
    class DiffArray:
        b: FixedLenArray[U8, 3]

    arr = AnArray([1, 2, 3])
    try:
        ser = AnArray.to_bytes(arr)
    except PodPathError as e:
        assert e.path == ["b", "AnArray"]

    arr = DiffArray([1, 2, 3])
    ser = DiffArray.to_bytes(arr)
    try:
        deser = AnArray.from_bytes(ser)
    except PodPathError as e:
        assert e.path == ["b", "AnArray"]
