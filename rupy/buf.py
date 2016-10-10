import re
import string
import binascii
import struct

from rupy.bitview import BitView
import itertools

from rupy.hexdump import HexDump

try:
    from zlib import crc32 as _crc32
except ImportError:
    def _crc32(buffer):
        raise NotImplementedError

try:
    from os import urandom
except ImportError:
    def urandom(length):
        raise RuntimeError("No randomness source available")




_REV8 = [int(bin(i)[2:].zfill(8)[::-1], 2) for i in range(256)]
_POPCNT = [bin(i).count('1') for i in range(256)]

class buf(bytearray):
    """
    buf(iterable_of_ints) -> buf.
    buf(string, encoding[, errors]) -> buf.
    buf(bytes_or_bytearray) -> mutable copy of bytes_or_bytearray.
    buf(memory_view) -> buf.

    Construct a mutable buf object from:
      - an iterable yielding integers in range(256)
      - a text string encoded using the specified encoding
      - a bytes or a buf object
      - any object implementing the buffer API.

    buf(int) -> buf.

    Construct a zero-initialized buf of the given length.

    >>> buf(10)
    buf(hex='00000000000000000000')
    >>> buf('hello')
    buf(b'hello')
    >>> buf([1,2,3,4])
    buf(hex='01020304')
    >>> buf(hex="deadbeef")
    buf(hex='deadbeef')
    """

    def capitalize(self):
        """
        B.capitalize() -> copy of B

        Return a copy of B with only its first character capitalized (ASCII)
        and the rest lower-cased.
        """
        return self.__class__(super(buf, self).capitalize())

    def center(self, width, fillchar=0):
        """
        B.center(width[, fillchar]) -> copy of B

        Return B centered in a string of length width.  Padding is
        done using the specified fill character (default is a null byte).
        """
        copy = self.__class__([fillchar]) * max(len(self), width)
        start = (len(copy) - len(self)) / 2
        copy[start:start + len(self)] = self
        return copy
    
    def count(self, sub, *args, **kwargs):
        """
        B.count(sub [,start [,end]]) -> int

        Return the number of non-overlapping occurrences of subsection sub in
        bytes B[start:end].  Optional arguments start and end are interpreted
        as in slice notation.
        """
        if isinstance(sub, (int, long)):
            sub = chr(sub)
        return super(buf, self).count(sub, *args, **kwargs)

    def expandtabs(self, *args, **kwargs):
        """
        B.expandtabs([tabsize]) -> copy of B

        Return a copy of B where all tab characters are expanded using spaces.
        If tabsize is not given, a tab size of 8 characters is assumed.
        """
        return self.__class__(super(buf, self).expandtabs(*args, **kwargs))


    @classmethod # known case
    def fromhex(cls, hexstring):
        """
        bytearray.fromhex(string) -> bytearray

        Create a bytearray object from a string of hexadecimal numbers.
        Spaces between two numbers are accepted.
        Example: bytearray.fromhex('B9 01EF') -> bytearray(b'\xb9\x01\xef').
        """
        return cls(hex=hexstring)

    def join(self, iterable_of_bytes):
        """
        B.join(iterable_of_bytes) -> bytes

        Concatenates any number of bytearray objects, with B in between each pair.
        """
        return self.__class__(super(buf, self).join(iterable_of_bytes))

    def ljust(self, width, fillchar=0):
        """
        B.ljust(width[, fillchar]) -> copy of B
        B.rpad(width[, fillchar]) -> copy of B  # alias

        Return B left justified (right padded) in a string of length width. Padding is
        done using the specified fill character (default is null).
        """
        copy = self.__class__([fillchar]) * max(len(self), width)
        copy[:len(self)] = self
        return copy

    rpad = ljust

    def lower(self):
        """
        B.lower() -> copy of B

        Return a copy of B with all ASCII characters converted to lowercase.
        """
        return self.__class__(super(buf, self).lower())

    def lstrip(self, bytes=b'\0'):
        """
        B.lstrip([bytes]) -> bytearray

        Strip leading bytes contained in the argument.
        If the argument is omitted, strip leading null bytes.
        """
        return self.__class__(super(buf, self).lstrip(bytes))

    def partition(self, sep):
        """
        B.partition(sep) -> (head, sep, tail)

        Searches for the separator sep in B, and returns the part before it,
        the separator itself, and the part after it.  If the separator is not
        found, returns B and two empty bytearray objects.
        """
        ind = self.find(sep)
        if ind == -1:
            ind = len(self)
        return self[:ind], self[ind:ind + len(sep)], self[ind + len(sep):]

    def replace(self, *args, **kwargs):
        """
        B.replace(old, new[, count]) -> bytes

        Return a copy of B with all occurrences of subsection
        old replaced by new.  If the optional argument count is
        given, only the first count occurrences are replaced.
        """
        return self.__class__(super(buf, self).replace(*args, **kwargs))

    def rjust(self, width, fillchar=0):
        """
        B.rjust(width[, fillchar]) -> copy of B
        B.lpad(width[, fillchar]) -> copy of B  # alias

        Return B right justified (left padded) in a string of length width. Padding is
        done using the specified fill character (default is a null byte)
        """
        copy = self.__class__([fillchar]) * max(len(self), width)
        copy[:len(self)] = self
        return copy
    lpad = rjust


    def rpartition(self, sep):
        """
        B.rpartition(sep) -> (head, sep, tail)

        Searches for the separator sep in B, starting at the end of B,
        and returns the part before it, the separator itself, and the
        part after it.  If the separator is not found, returns two empty
        bytearray objects and B.
        """
        ind = self.rfind(sep)
        if ind == -1:
            ind = len(self)
        return self[:ind], self[ind:ind + len(sep)], self[ind + len(sep):]

    def rsplit(self, *args, **kwargs):
        """
        B.rsplit(sep[, maxsplit]) -> list of bytearray

        Return a list of the sections in B, using sep as the delimiter,
        starting at the end of B and working to the front.
        If sep is not given, B is split on ASCII whitespace characters
        (space, tab, return, newline, formfeed, vertical tab).
        If maxsplit is given, at most maxsplit splits are done.
        """
        return [self.__class__(x) for x in super(buf, self).rsplit(*args, **kwargs)]

    def rstrip(self, bytes=b'\0'):
        """
        B.rstrip([bytes]) -> bytearray

        Strip trailing bytes contained in the argument.
        If the argument is omitted, strip trailing null bytes.
        """
        return self.__class__(super(buf, self).lstrip(bytes))

    def split(self, *args, **kwargs):
        """
        B.split([sep[, maxsplit]]) -> list of bytearray

        Return a list of the sections in B, using sep as the delimiter.
        If sep is not given, B is split on ASCII whitespace characters
        (space, tab, return, newline, formfeed, vertical tab).
        If maxsplit is given, at most maxsplit splits are done.
        """
        return [self.__class__(x) for x in super(buf, self).split(*args, **kwargs)]


    def splitlines(self, *args, **kwargs):
        """
        B.splitlines(keepends=False) -> list of lines

        Return a list of the lines in B, breaking at line boundaries.
        Line breaks are not included in the resulting list unless keepends
        is given and true.
        """
        return [self.__class__(x) for x in super(buf, self).splitlines(*args, **kwargs)]

    def strip(self, bytes=b'\0'):
        """
        B.strip([bytes]) -> bytearray

        Strip leading and trailing bytes contained in the argument.
        If the argument is omitted, strip null bytes.
        """
        return self.__class__(super(buf, self).lstrip(bytes))

    def swapcase(self):
        """
        B.swapcase() -> copy of B

        Return a copy of B with uppercase ASCII characters converted
        to lowercase ASCII and vice versa.
        """
        return self.__class__(super(buf, self).swapcase())

    def title(self): # real signature unknown; restored from __doc__
        """
        B.title() -> copy of B

        Return a titlecased version of B, i.e. ASCII words start with uppercase
        characters, all remaining cased characters have lowercase.
        """
        return self.__class__(super(buf, self).title())

    def translate(self, *args, **kwargs): # real signature unknown; restored from __doc__
        """
        B.translate(table[, deletechars]) -> bytearray

        Return a copy of B, where all characters occurring in the
        optional argument deletechars are removed, and the remaining
        characters have been mapped through the given translation
        table, which must be a bytes object of length 256.
        """
        return self.__class__(super(buf, self).translate(*args, **kwargs))

    def upper(self): # real signature unknown; restored from __doc__
        """
        B.upper() -> copy of B

        Return a copy of B with all ASCII characters converted to uppercase.
        """
        return self.__class__(super(buf, self).upper())

    def zfill(self, width): # real signature unknown; restored from __doc__
        """
        B.zfill(width) -> copy of B

        Pad a numeric string B with zeros on the left, to fill a field
        of the specified width.  B is never truncated.
        """
        return self.__class__(super(buf, self).zfill(width))

    def __add__(self, y): # real signature unknown; restored from __doc__
        """ x.__add__(y) <==> x+y """
        res = self.__class__(self)
        res.__iadd__(y)
        return res

    def __getitem__(self, y): # real signature unknown; restored from __doc__
        """ x.__getitem__(y) <==> x[y] """
        if isinstance(y, slice):
            if y.step in (None, 1):
                # Avoid unnecessary copy
                return self.__class__(memoryview(self)[y])
            else:
                # Fallback for skip values / integer indices
                return self.__class__(super(buf, self).__getitem__(y))
        else:
            return super(buf, self).__getitem__(y)

    def __mul__(self, n): # real signature unknown; restored from __doc__
        """ x.__mul__(n) <==> x*n """
        res = self.__class__(self)
        res.__imul__(n)
        return res

    def __repr__(self): # real signature unknown; restored from __doc__
        """ x.__repr__() <==> repr(x) """
        if self.isprintable():
            return "{}(b{!r})".format(self.__class__.__name__, str(self))
        else:
            return "{}(hex='{}')".format(self.__class__.__name__, self.tohex())


    def __rmul__(self, n): # real signature unknown; restored from __doc__
        """ x.__rmul__(n) <==> n*x """
        return self.__mul__(n)

    # da magic

    def __init__(self, *args, **kwargs):
        """
        buf(iterable_of_ints) -> buf.
        buf(string, encoding[, errors]) -> buf.
        buf(bytes_or_bytearray) -> mutable copy of bytes_or_bytearray.
        buf(memory_view) -> buf.
        buf(hex=hex_value) -> buf

        Construct a mutable buf object from:
          - an iterable yielding integers in range(256)
          - a text string encoded using the specified encoding
          - a bytes or a bytearray object
          - any object implementing the buffer API.
          - a hexadecimal string.

        buf(int) -> buf.

        Construct a zero-initialized buf of the given length.
        """
        hex = kwargs.pop('hex', None)

        if ('source' in kwargs or len(args) > 0) and hex is not None:
            raise ValueError("can't supply both `source` and `hex`")

        if hex is not None:
            hex = re.sub('\s+', '', hex, flags=re.S)
            source = binascii.unhexlify(hex)
            super(buf, self).__init__(source, *args, **kwargs)
        else:
            super(buf, self).__init__(*args, **kwargs)


    def __hex__(self):
        return self.tohex()

    def tohex(self, uppercase=False):
        """
        b.tohex([uppercase=False]) -> str

        Convert the buf to hexadecimal representation..
        """
        res = binascii.hexlify(self)
        if uppercase:
            res = res.upper()
        return res

    def issimpleascii(self):
        """
        b.issimpleascii() -> bool

        Returns True if b is composed of simple single-width ASCII characters.
        """
        return not self.translate(bytearray(range(256)), bytearray(range(32, 126)))

    def isprintable(self):
        """
        b.isprintable() -> bool

        Returns True if b is composed of printable ASCII characters (string.printable).
        """
        return not self.translate(bytearray(range(256)), string.printable)


    def toint(self, little_endian=True, signed=False):
        """
        b.toint([little_endian=True[, signed=True]])

        Convert bytes to integer.
        This function is made to be behaviorally compatible with Python 3's int.from_bytes.

        >>> buf(hex='1234').toint() == 0x3412
        True
        >>> buf(hex='ffffffff').toint(signed=False) == 0xffffffff
        True
        >>> buf(hex='ffffffff').toint(signed=True) == -1
        True
        """
        bl = self[::]
        if little_endian:
            bl.reverse()

        val = 0L
        for b in bl:
            val <<= 8
            val |= b

        if signed:
            bl = (val.bit_length() + 7) / 8 * 8
            if val & (1 << (bl - 1)):
                return -((1 << bl) - val)

        return val

    @classmethod
    def fromint(cls, n, size=None, little_endian=True, signed=False):
        """
        buf.fromint(n[, size[, little_endian=True[, signed=False]]])

        Convert an integer to a byte array.
        The optional size arguemnt determines the size of the resulting array
        (By default the size is the minimum possible).
        This function is made to be behaviorally compatible with Python 3's int.to_bytes.

        >>> buf.fromint(0x1234)
        buf(hex='3412')
        >>> buf.fromint(1, 4, False)
        buf(hex='00000001')
        """
        bl = max(n.bit_length(), 1)
        if not signed and n < 0:
            raise OverflowError("can't convert negative int to unsigned")
        if signed:
            bl += 1

        rsize = (bl + 7) / 8

        if size is None:
            size = rsize
        elif size < rsize:
            raise OverflowError("int too big to convert")

        if signed and n < 0:
            n += (1 << (size * 8))

        bl = cls(size)

        if little_endian:
            it = range(size)
        else:
            it = range(size - 1, -1, -1)

        for i in it:
            bl[i] = n & 0xff
            n >>= 8
        return bl

    def __long__(self):
        """ long(b) <==> b.__long__() <==> b.toint()"""
        return self.toint()

    def __int__(self):
        """ int(b) <==> b.__int__() <==> b.toint()"""
        return self.toint()

    def __xor__(self, other):
        """ b.__xor__(y) <==> b ^ y"""
        if isinstance(other, (int, long)):
            other = itertools.cycle([other])
        else:
            other = self.__class__(itertools.islice(other, len(self)))
        return self.__class__(x ^ y for x, y in zip(self, other))

    def __and__(self, other):
        """ b.__and__(y) <==> b & y"""
        if isinstance(other, (int, long)):
            other = itertools.cycle([other])
        else:
            other = self.__class__(itertools.islice(other, len(self)))
        return self.__class__(x & y for x, y in zip(self, other))

    def __or__(self, other):
        """ b.__or__(y) <==> b | y"""
        if isinstance(other, (int, long)):
            other = itertools.cycle([other])
        else:
            other = self.__class__(itertools.islice(other, len(self)))
        return self.__class__(x | y for x, y in zip(self, other))

    def __invert__(self):
        """ b.__invert__() <==> ~b """
        return self.__class__((~x) & 0xff for x in self)

    def hexdump(self, *args, **kwargs):
        """
        b.hexdump([hexdump_params])

        Return a HexDump object of the buf

        >>> b = buf(hex='68656c6c6f20776f726c64211337abcd')
        >>> print b.hexdump()
        000000| 6865 6c6c 6f20 776f  726c 6421 1337 abcd |hello world!.7..|
        """
        return HexDump(self, *args, **kwargs)

    @classmethod
    def random(cls, size=None):
        """
        buf.random(size) -> buf

        Returns a randomized buf of the given size.
        >>> x = buf.random(1024)
        >>> print len(x)
        1024
        >>> # This test isn't deterministic but is very likely and a good measure of uniformity
        >>> all(x.count(b) < 20 for b in range(256))
        True
        """
        try:
            import os
            return cls(os.urandom(size))
        except ImportError:
            import random
            return cls(random.randrange(256) for i in xrange(size))

    def at(self, offset, length=1):
        """b.at(offset, length=1) <==> b[offset:offset + length]"""
        res = self[offset:offset + length]
        if len(res) != length:
            raise OverflowError("not enough data in buffer")

    def blocks(self, blocksize, fillchar=None):
        """
        b.blocks(blocksize[, padding=None]) -> iterable_of_bufs

        Returns a generator of blocks, each one with the specified blocksize,
        optionally right-padded with the specified fillchar.
        >>> g = buf('aaaabbbbccccdd').blocks(4)
        >>> for x in g:
        ...    print x
        aaaa
        bbbb
        cccc
        dd

        >>> g = buf('something completely different').blocks(8, 'x')
        >>> for x in g:
        ...    print x
        somethin
        g comple
        tely dif
        ferentxx
        """
        if fillchar is None:
            return (self[i:i+blocksize] for i in xrange(0, len(self), blocksize))
        else:
            return (self[i:i+blocksize].rpad(blocksize, fillchar) for i in xrange(0, len(self), blocksize))

    def unpack(self, fmt, offset=None):
        """
        b.unpack(fmt[, offset]) -> tuple

        Unpack binary values according to fmt, optionally starting from offset.

        >>> b = buf(hex="12345678abcd")
        >>> print b.unpack('<HHH')
        (13330, 30806, 52651)
        >>> b.unpack('<L', 2) == (3450566742,)
        True
        """
        if offset is None:
            return struct.unpack(fmt, self)
        else:
            return struct.unpack_from(fmt, self, offset)

    @classmethod
    def pack(cls, fmt, *values):
        """
        b.pack(fmt, values...) -> buf

        Pack values into a new buf accroding to fmt.

        >>> b = buf.pack('>L', 0xdeadbeef)
        >>> hex(b) == "deadbeef"
        True
        >>> print buf.pack('5c', 'h', 'e', 'l', 'l', 'o')
        hello
        """
        res = cls(struct.calcsize(fmt))
        struct.pack_into(fmt, res, 0, *values)
        return res

    def fields(self, fieldspec, offset=0, strict=False):
        """
        b.fields(fieldspec[, offset[, strict=False]]) -> BoundFieldMap

        Create a field mapping of the buf instance with the specified field spec.
        **NOTE**: Upon creating a bound field mapping, the buffer's size cannot change as long as it is referenced
        by it.

        TODO - Document this function
        If strict is True, total sizes must match.

        >>> b = buf(hex='deadbeefaabbccdd01234567')
        >>> s = b.fields("x:uint32  y:uint32b  z:Bytes(4)")
        >>> s.x == 0xefbeadde
        True
        >>> s.z == buf(hex='01234567')
        True
        >>> s.y = 0xcafebabe
        >>> print hex(b)
        deadbeefcafebabe01234567
        >>> b.fields("uint16b", 2)[0] = 0xd00d
        >>> print hex(b)
        deadd00dcafebabe01234567
        """

        from rupy import fields
        if isinstance(fieldspec, str):
            # convenience, allows writing stuff like "a:int32 b:int64 c:Bytes(16)" etc.
            #TODO Improve this silly DSL to support nested stuff (really?..)
            fieldspec = [tuple(x.split(':',1)) if ':' in x else x for x in fieldspec.split()]

        map = fields.FieldMap(fieldspec)
        data = memoryview(self)[offset:offset + map.size]
        if strict and len(data) != map.size:
            raise OverflowError("Field map size mismatch (and 'strict' is True)")
        return map.unpack(data)

    @property
    def bits(self):
        """
        b.bits() -> BitView

        Return a BitView object of the buffer. See BitView's docstring.
        >>> b = buf(hex='aa55')
        >>> print b.bits
        1010101001010101
        >>> print b.bits[4:-4]
        10100101
        >>> b.bits.invert()
        >>> b
        buf(hex='55aa')
        >>> b.bits[:8].set()
        >>> b
        buf(hex='ffaa')
        """
        return BitView(self)

    def rev8(self):
        """
        b.rev8()  -> buf

        Returns a new buffer with each byte bit-reversed.

        >>> buf(hex='a5228001').rev8()
        buf(hex='a5440180')
        """
        return buf(_REV8[x] for x in self)

    def popcount(self):
        """
        b.popcount() -> int

        Returns the number of on bits in the buffer.

        >>> buf(hex='fff0').popcount()
        12
        """
        return sum(_POPCNT[x] for x in self)

    def crc32(self):
        """
        b.crc32() -> int

        Return the CRC32 checksum of the buffer.
        """
        return _crc32(buffer(self))
