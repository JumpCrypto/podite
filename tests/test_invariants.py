"""
Property based tests
- serialize and deserialize are always inverses (with exceptions, e.g. float)
"""

from hypothesis import given, note, strategies as st

from pod.decorators import pod
from pod.types.atomic import (
    Bool,
    I128,
    I128b,
    I128l,
    I16,
    I16b,
    I16l,
    I32,
    I32b,
    I32l,
    I64,
    I64b,
    I64l,
    I8,
    I8b,
    I8l,
    U128,
    U128b,
    U128l,
    U16,
    U16b,
    U16l,
    U32,
    U32b,
    U32l,
    U64,
    U64b,
    U64l,
    U8,
    U8b,
    U8l,
)


@pod
class Atomic:
    # bool
    bool: Bool

    # 1-byte integers
    i8l: I8l
    i8b: I8b
    i8: I8

    u8l: U8l
    u8b: U8b
    u8: U8

    # 2-byte integers
    i16l: I16l
    i16b: I16b
    i16: I16

    u16l: U16l
    u16b: U16b
    u16: U16

    # 4-byte integers
    i32l: I32l
    i32b: I32b
    i32: I32

    u32l: U32l
    u32b: U32b
    u32: U32

    # 8-byte integers
    i64l: I64l
    i64b: I64b
    i64: I64

    u64l: U64l
    u64b: U64b
    u64: U64

    # 16-byte integers
    i128l: I128l
    i128b: I128b
    i128: I128

    u128l: U128l
    u128b: U128b
    u128: U128


@pod
class AtomicBool:
    a: Bool


@given(st.booleans().map(AtomicBool))
def test_bool_bytes(atomic_bool):
    note(f"AtomicBool: {atomic_bool}")
    assert atomic_bool.from_bytes(AtomicBool.to_bytes(atomic_bool)) == atomic_bool


@given(st.booleans().map(AtomicBool))
def test_bool_json(atomic_bool):
    note(f"AtomicBool: {atomic_bool}")
    assert atomic_bool.from_dict(AtomicBool.to_dict(atomic_bool)) == atomic_bool


atomic_strategy = st.tuples(
    st.booleans(),
    st.integers(min_value=-(2**7), max_value=2**7 - 1),
    st.integers(min_value=-(2**7), max_value=2**7 - 1),
    st.integers(min_value=-(2**7), max_value=2**7 - 1),
    st.integers(min_value=0, max_value=2**8 - 1),
    st.integers(min_value=0, max_value=2**8 - 1),
    st.integers(min_value=0, max_value=2**8 - 1),
    st.integers(min_value=-(2**15), max_value=2**15 - 1),
    st.integers(min_value=-(2**15), max_value=2**15 - 1),
    st.integers(min_value=-(2**15), max_value=2**15 - 1),
    st.integers(min_value=0, max_value=2**16 - 1),
    st.integers(min_value=0, max_value=2**16 - 1),
    st.integers(min_value=0, max_value=2**16 - 1),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    st.integers(min_value=0, max_value=2**32 - 1),
    st.integers(min_value=0, max_value=2**32 - 1),
    st.integers(min_value=0, max_value=2**32 - 1),
    st.integers(min_value=-(2**63), max_value=2**63 - 1),
    st.integers(min_value=-(2**63), max_value=2**63 - 1),
    st.integers(min_value=-(2**63), max_value=2**63 - 1),
    st.integers(min_value=0, max_value=2**64 - 1),
    st.integers(min_value=0, max_value=2**64 - 1),
    st.integers(min_value=0, max_value=2**64 - 1),
    st.integers(min_value=-(2**127), max_value=2**127 - 1),
    st.integers(min_value=-(2**127), max_value=2**127 - 1),
    st.integers(min_value=-(2**127), max_value=2**127 - 1),
    st.integers(min_value=0, max_value=2**128 - 1),
    st.integers(min_value=0, max_value=2**128 - 1),
    st.integers(min_value=0, max_value=2**128 - 1),
).map(lambda args: Atomic(*args))


@given(atomic_strategy)
def test_bytes(atomic):
    note(f"Atomic: {atomic}")
    assert Atomic.from_bytes(Atomic.to_bytes(atomic)) == atomic


@given(atomic_strategy)
def test_json(atomic):
    note(f"Atomic: {atomic}")
    assert Atomic.from_dict(Atomic.to_dict(atomic)) == atomic
