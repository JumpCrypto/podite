# Pod
### Serializing and Deserializing Plain Old Data

Pod allows easily describing the byte format of dataclasses with all the usual 
conveniences of working with native python objects. 

### Quick Start
Defining a message is as simple as:
```python
from pod import pod, U8, Str

@pod
class Message:
    message: Str[1000] # max_length of string
    likes: U8

original = Message("Serialization doesn't have to be painful", 19020)
Message.to_bytes(original)
```
This has a byte representation of:
```
| length of string | utf-8 string contents | likes  | 
-----------------------------------------------------
| 4 bytes          | str-len bytes         | 1 byte |
```

Here is a corresponding rust struct that can deserialize this message:
```rust
use borsh::BorshDeserialize;

#[derive(BorshDeserialize)]
struct Message {
    message: String,
    likes: u8,
}
```

Pod was originally developed to interact with rust smart-contracts on solana where compact,
quick and consistent ser(de) (serialization and deserialization) are crucial. Pod by default serializes to 
borsh format used by most solana programs, but also supports zero-copy ser(de) to C format structs.

```python
from pod import FORMAT_ZERO_COPY
# ... previous 

_bytes = Message.to_bytes(original, format=FORMAT_ZERO_COPY)
round_tripped = Message.from_bytes(_bytes)
```

```rust
use bytemuck::{Pod, ZeroCopy};

#[derive(Pod, ZeroCopy, Clone, Copy, Debug)]
struct Message {
    message: String,
    likes: u8,
}
```
Notice that to deserialize, the format did not need to be specified. As there are currently only 2  
binary formats supported by pod, we can compare the number of bytes we are given to the fixed size
of a zero-copy serialized object. If they are the same, we can deserialize using zero-copy and if they 
are different, we can attempt to deserialize using the borsh format. 

If you do not want to rely on
this implicit format recognition, you can explicitly write the format like this:
```python
Message.from_bytes(_bytes, format=...)
```