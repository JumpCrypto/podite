<h1 style="border-bottom: none" align="center">Podite</h1>
<p align="center">Noun: the leg of a c<b>Rustacean</b></p>


### Serializing and Deserializing "Plain Old Data"

Podite makes interacting with on-chain programs easy - if a Podite dataclass looks exactly 
like it’s on-chain rust equivalent, then you know it serializes the same way too. 
No more arcane serialization libraries, no more surprises - get exactly what you expect.

Podite was developed alongside [Solmate](https://github.com/nimily/solmate), a client code generator
for Solana smart-contracts using the [Anchor Framework](https://github.com/project-serum/anchor) in rust.

### Key Principles
***Simple*** - 
python types visually mirror on-chain rust types

***Pythonic*** - 
follows conventions from native `dataclass`

***Smart Defaults*** - 
automatically detects Borsh and ZeroCopy (bytemuck) account formats during deserialization, but allows manually specifying format

***Extensible*** -
provide custom serialization to support non-standard account layouts or optimize in performance-critical components


### Quick Start
Defining a message is as simple as:

```python
from podite import pod, U8, Str

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
from podite import FORMAT_ZERO_COPY
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

### Installation
Requires `python >= 3.9`
```sh
poetry install podite
```
or
```sh
pip install podite
```

### Development Setup

If you want to contribute to Solmate, follow these steps to get set up:

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Install dev dependencies:
```sh
poetry install
```
3. Code your change and add tests
4. Verify tests 
```sh
poetry run pytest
```
5. Open Pr!
