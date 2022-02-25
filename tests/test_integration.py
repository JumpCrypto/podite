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
    serialized = MyStruct.to_bytes(val)
    deserialized = MyStruct.from_bytes(serialized)

    assert val == deserialized


def test_fixed_len_array_wrong_size():
    @pod
    class AnArray:
        b: FixedLenArray[U8, 10]

    arr = AnArray([1, 2, 3])
    print(arr)
    try:
        ser = AnArray.to_bytes(arr)
    except PodPathError as e:
        assert e.path == ["b", "AnArray"]
