

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
>>> f = b.fields('a: u32  b: u16  c: Bytes[6]')
>>> print(hex(f.a), hex(f.b), repr(f.c))
0xefbeadde 0x3412 buf(hex='5678aabb1337')
```

### `Range`
Enhanced range(); a class that behaves like a normal range() but also enables slicing, infinite ranges, 
series notation (e.g: `Range[1, 2, ..., 100]` is like `Range(1, 101)`) and more.

Range is similar to builtin range() functions, except it also supports:
    * Sub-slicing
    * Unbounded ranges
    * Series notation using ellipsis
    * Arithmetic operations on ranges
    * And much more!

All this goodness is with negligible overhead, since Range() uses builtin types for the actual
iteration, such as xrange()/range() and itertools.count().

Usage examples:

```python
>>> print(Range(10))
Range[0, 1, ..., 9]

>>> print(Range(None))
Range[0, 1, 2, ...]

>>> print(Range(step=-1))
Range[0, -1, -2, ...]

>>> for i in Range[1, 2, ..., 10]:
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

>>> 1024 in Range[2:32768:2]
True

>>> for i in Range[1, 2, ...]:
...    if i == 2**16:
...        print("No more!")
...        break
No more!

>>> print(Range[0, ...][2:12:2])
Range[2, 4, ..., 10]
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

## Compatibility
This package is compatible with Python versions 2.7 and 3.3+.
