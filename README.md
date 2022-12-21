

# rupy

Random Useful Python stuff

## What's inside?
A collection of utilities I find useful.

### `buf`
A bytearray-derived class with many useful methods, supporting bitwise operations and much more.

```python
>>> buf(10)
buf(hex='00000000000000000000')

>>> str(buf(b'hello'))  # utf-8 decode
'hello'

>>> buf([1,2,3,4])
buf(hex='01020304')

>>> buf(hex="deadbeef")
buf(hex='deadbeef')

>>> print(buf.random(100).hexdump())
#000000| 6568 15de cf7a ce7e  fb66 d9f3 cad4 d144 |eh...z.~.f.....D|
#000010| bc0b c4fd 05c0 5fb5  eca1 870c 94e6 5b73 |......_.......[s|
#000020| 3a86 322c 0ede de2e  dd4b d1a6 331d 3c1b |:.2,.....K..3.<.|
#000030| 6eb2 27c4 3246 1526  56a8 85a6 8c06 2d91 |n.'.2F.&V.....-.|
#000040| a8fc 821d f806 a442  93ff 3503 27fe b3dd |.......B..5.'...|
#000050| 1a8e 0aef da63 8eba  8d4f 6da5 fd44 8634 |.....c...Om..D.4|
#000060| 3a6e 2395                                |:n#.            |

>>> b = buf(b"hello")
>>> s = b.to_stream()
>>> s.seek(0, 2)
>>> s.write(b" world")
>>> print(b)
hello world
```

Also available: `hexdump`, which produces nice hexdumps.

### `bitview`
Allows for bit addressing and manipulation in-memory.

```python
>>> b = buf(hex='aa55')
>>> print(b.bits)
1010101001010101

>>> print(b.bits[4:-4])  # bit views support slicing
10100101

>>> b.bits.invert()
>>> b
buf(hex='55aa')

>>> b.bits[:8].set()  # set bits to 1
>>> b
buf(hex='ffaa')
```

### `fields`
A small binary structure manipulation library, integrated nicely with the `buf` structure, allowing for stuff like:

```python
>>> from rupy import buf
>>> b=buf(hex='12345678aabbccdd')
>>> b.fields('i32 u8[4]')
<2 fields:
   [0]: 2018915346
   [1]: (170, 187, 204, 221)
>

>>> b.fields('foo: i32 bar: u8[4]')  # named fields
Out[4]:
<2 fields:
   foo = 2018915346
   bar = (170, 187, 204, 221)
>

>>> b.fields('foo: i32 bar: u8[4]').foo = 5  # in-memory change
>>> b
buf(hex='05000000aabbccdd')

>>> b.fields('foo: i32b bar: u8[4]').foo = 5  # big endian
>>> b
buf(hex='00000005aabbccdd')

>>> b.fields('foo: i32b bar: {a: u16 b: u16}')  # nested structs
<2 fields:
   foo = 5
   bar = <2 fields:
      a = 48042
      b = 56780
   >
>
```

### `Seq`
Integer sequences. a class that behaves like a normal range() but also enables slicing, infinite ranges, 
intuitive notation (e.g: `Seq[1, 2, ..., 100]` is like `Seq(1, 101)`) and more.

Seq is similar to builtin range() functions, except it also supports:
    * Sub-slicing
    * Unbounded ranges
    * Series notation using ellipsis
    * Arithmetic operations on ranges
    * And much more!

Usage examples:

```python
>>> print(Seq(10))  # like range()
Seq[0, 1, ..., 9]

>>> print(Seq(None))  # no upper bound, infinite range
Seq[0, 1, 2, ...]

>>> print(Seq(step=-1))
Seq[0, -1, -2, ...]

>>> for i in Seq[1, 2, ..., 10]:  # sequence notation
...    print(i)
1
2
3
4
5
6
7
8
9
10

>>> 1024 in Seq[2:32768:2]  # fast containment check
True

>>> for i in Seq[1, 2, ...]:
...    if i == 2**16:
...        print("No more!")
...        break
No more!

>>> print(Seq[0, ...][2:12:2])  # Seqs support slicing
Seq[2, 4, ..., 10]
```

### `Stream`
A stream wrapper that allows blockwise iteration as well as slicing and single-byte indexing. 

```python
>>> s = Stream.open("foo.bin", "rb")
>>> x = s[10:30]
>>> x
<StreamSlice [10:30] of '/tmp/bla.bin'>
>>> buf(x)
buf(hex='63a7349ca38cc6319f3430c72e9659e8aca27705')
>>> s[:1000].copy(open('/tmp/bar.bi', 'wb'))  # Write stream data to other stream (buffered)
```

## `pp`
Pretty-printing for large nested structures with Unicode trees and colors.

## Compatibility
This package is compatible with Python versions 2.7 and 3.3+.


