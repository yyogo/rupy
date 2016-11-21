

# rupy

Random Useful Python stuff

## What's inside?
A collection of utilities I find useful.

### `buf`
A bytearray-derived class with many useful methods, supporting bitwise operations and much more.

```python
>>> buf(10)
buf(hex='00000000000000000000')

>>> str(buf(b'hello'))
'hello'

>>> buf([1,2,3,4])
buf(hex='01020304')

>>> buf(hex="deadbeef")
buf(hex='deadbeef')

>>> print(buf.random(100).hexdump())
000000| 6568 15de cf7a ce7e  fb66 d9f3 cad4 d144 |eh...z.~.f.....D|
000010| bc0b c4fd 05c0 5fb5  eca1 870c 94e6 5b73 |......_.......[s|
000020| 3a86 322c 0ede de2e  dd4b d1a6 331d 3c1b |:.2,.....K..3.<.|
000030| 6eb2 27c4 3246 1526  56a8 85a6 8c06 2d91 |n.'.2F.&V.....-.|
000040| a8fc 821d f806 a442  93ff 3503 27fe b3dd |.......B..5.'...|
000050| 1a8e 0aef da63 8eba  8d4f 6da5 fd44 8634 |.....c...Om..D.4|
000060| 3a6e 2395                                |:n#.            |
```

### `bitview`
Allows for bit addressing and manipulation in-memory.

```python
>>> b = buf(hex='aa55')
>>> print(b.bits)
1010101001010101
>>> print(b.bits[4:-4])
10100101
>>> b.bits.invert()
>>> b
buf(hex='55aa')
>>> b.bits[:8].set()
>>> b
buf(hex='ffaa')
```

### `fields`
A small binary structure manipulation library, integrated nicely with the `buf` structure, allowing for stuff like:

```python
>>> b = buf(hex='deadbeef12345678aabb1337')
>>> f = b.fields('a: uint32  b: uint16  c: Bytes[6]')
>>> print(hex(f.a), hex(f.b), repr(f.c))
0xefbeadde 0x3412 buf(hex='5678aabb1337')
```

### `Range`
Enhanced range(); a class that behaves like a normal range() but also enables slicing, infinite ranges, 
series notation (e.g: `Range[1, 2, ..., 100]` is like `Range(1, 101)`) and more.

### `Stream`
A stream wrapper that allows blockwise iteration as well as slicing and single-byte indexing.

## Compatibility
This package is compatible with Python versions 2.7 and 3.3+.
