def readme():
    from podite import pod, U8, Str

    @pod
    class Message:
        message: Str[1000]  # max_length of string
        likes: U8

    original = Message("Serialization doesn't have to be painful", 19020)
    Message.to_bytes(original)

    from podite import FORMAT_ZERO_COPY

    # ... previous

    _bytes = Message.to_bytes(original, format=FORMAT_ZERO_COPY)
    round_tripped = Message.from_bytes(_bytes)

    assert original == round_tripped
