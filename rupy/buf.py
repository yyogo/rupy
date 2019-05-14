import io
import re
import string
import base64
import binascii
import struct
import itertools

from rupy.bitview import BitView
from rupy.hexdump import HexDump

from rupy.compat import *

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



_REV8 = tuple(int(bin(i)[2:].zfill(8)[::-1], 2) for i in range(256))
_POPCNT = tuple(bin(i).count('1') for i in range(256))

ByteType = type(b'x'[0])  # int in python3, str in python2

@compatible
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
    >>> str(buf(b'hello'))
    'hello'
    >>> buf([1,2,3,4])
    buf(hex='01020304')
    >>> buf(hex="deadbeef")
    buf(hex='deadbeef')
    """

    # Maximum length before snipping, set to None to disable snipping
    _REPR_FULL_MAX = 100
    # Set to True to always display string as hex, False to never
    _REPR_HEX = None
    # Set to 0 to disable hexdump in __repr__
    _REPR_HEXDUMP_LINES = 10

    def _create_fill(self, width, pattern):
        real_len = max(len(self), width)
        if pattern is None:
            return self.__class__(real_len)
        elif hasattr(pattern, '__len__') and len(pattern) == 0:
            return self.__class__(0)
        if isinstance(pattern, int):
            pattern = bytes([pattern])
        times = (real_len + len(pattern) - 1) // len(pattern)
        fill = self.__class__(pattern) * times
        fill[real_len:] = []
        return fill

    def capitalize(self):
        """
        B.capitalize() -> copy of B

        Return a copy of B with only its first character capitalized (ASCII)
        and the rest lower-cased.
        """
        return self.__class__(super(buf, self).capitalize())

    def center(self, width, fill=None):
        """
        B.center(width[, fill]) -> copy of B

        Return B centered in a string of length width.  Padding is
        done using the specified fill pattern (default is null byte).
        """
        copy = self._create_fill(width, fill)
        start = (len(copy) - len(self)) // 2
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
            sub = bytearray((sub,))
        return super(buf, self).count(sub, *args, **kwargs)

    def copy(self):
        return self[:]

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
        bytearray.from_hex(string) -> bytearray  # alias

        Create a bytearray object from a string of hexadecimal numbers.
        Spaces between two numbers are accepted.
        Example: bytearray.fromhex('B9 01EF') -> bytearray(b'\\xb9\\x01\\xef').
        """
        return cls(hex=hexstring)

    # Python 3 bytes() has fromhex, but convention recommends from_hex
    from_hex = fromhex

    def join(self, iterable_of_bytes):
        """
        B.join(iterable_of_bytes) -> bytes

        Concatenates any number of bytearray objects, with B in between each pair.
        """
        return self.__class__(super(buf, self).join(iterable_of_bytes))

    def ljust(self, width, fill=None):
        """
        B.ljust(width[, fill]) -> copy of B
        B.rpad(width[, fill]) -> copy of B  # alias

        Return B left justified (right padded) in a string of length width. Padding is
        done using the specified fill pattern (default is null bytes).
        """
        copy = self._create_fill(width, fill)
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

    def rjust(self, width, fill=None):
        """
        B.rjust(width[, fill]) -> copy of B
        B.lpad(width[, fill]) -> copy of B  # alias

        Return B right justified (left padded) in a string of length width. Padding is
        done using the specified fill pattern (default is null bytes).
        """
        copy = self._create_fill(width, fill)
        copy[-len(self):] = self
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

    def __ascii__(self, snip=None):
        if snip and len(self) > snip:
            s = ascii(bytes(self[:snip*2//3])) + '...' + ascii(bytes(self[-snip//3:]))
        else:
            s = ascii(bytes(self))
        return "{}({})".format(self.__class__.__name__, s)

    def __hex__(self, snip=None):
        if snip and len(self) > snip:
            h = self[:snip*2//3].hex() + '...' + self[-snip//3:].hex()
        else:
            h = self.hex()
        return "{}(hex='{}')".format(self.__class__.__name__, h)

    def __repr__(self): # real signature unknown; restored from __doc__
        """ x.__repr__() <==> repr(x) """
        use_hex = self._REPR_HEX
        if use_hex is None:
            use_hex = not self.isprintable()
        if use_hex:
            if self._REPR_HEXDUMP_LINES and self._REPR_FULL_MAX and self._REPR_FULL_MAX < len(self):
                hd = self.hexdump().dump(snip=self._REPR_HEXDUMP_LINES, skip_dups=True).strip()
                return "<{}, {} bytes:\n{} >".format(self.__class__.__name__, len(self), hd)
            return self.__hex__(snip=self._REPR_FULL_MAX)
        return self.__ascii__(snip=self._REPR_FULL_MAX)


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
        hex_string = kwargs.pop('hex', None)

        if hex_string is not None:
            if 'source' in kwargs or len(args) > 0:
                raise ValueError("can't supply both `source` and `hex`")
            hex_string = re.sub('\s+', '', hex_string, flags=re.S)
            source = binascii.unhexlify(hex_string)
            super(buf, self).__init__(source, *args, **kwargs)
        elif len(args) == 1 and hasattr(args[0], '__bytes__'):
            super(buf, self).__init__(args[0].__bytes__())
        else:
            super(buf, self).__init__(*args, **kwargs)

    def hex(self, uppercase=False):
        """
        b.hex([uppercase=False]) -> str
        b.to_hex([uppercase=False]) -> str  # alias

        Convert the buf to hexadecimal representation..
        """
        res = getattr(bytearray, "hex", binascii.hexlify)(self)
        if uppercase:
            return res.upper()
        return res

    to_hex = hex

    @classmethod
    def from_base64(cls, s, altchars="+/", paddingcheck=False):
        """
        Convert a base-64 encoded byte string to a buf.

        >>> print(buf.from_base64("SGVsbG8gV29ybGQ", paddingcheck=False)) # Missing padding, should still work
        Hello World

        >>> print(buf.from_base64("3q2-7w==", altchars="-_").hex())
        deadbeef
        """
        if not paddingcheck:
            s += "======"
        return cls(base64.b64decode(s, altchars=altchars))

    def base64(self, altchars="+/", multiline=True):
        """
        Convert a base-64 encoded byte string to a buf.

        >>> print(buf(b'Hello World').base64())
        SGVsbG8gV29ybGQ=

        >>> print(buf(hex="deadbeef").base64(altchars="-_"))
        3q2-7w==
        """
        res = base64.b64encode(self, altchars.encode('ascii')).decode('ascii')
        if not multiline:
            res = res.replace("\n", "")
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
        return not self.translate(bytearray(range(256)), string.printable.encode("ascii"))

    if hasattr(int, 'to_bytes') and hasattr(int, 'from_bytes'):
        # yay Python 3 :)
        @classmethod
        def _from_int(cls, n, size, byteorder, signed):
            return cls(int.to_bytes(n, size, byteorder, signed=signed))

        def _to_int(self, byteorder, signed):
            return int.from_bytes(self, byteorder, signed=signed)
    else:
        # No python 3 cool stuff :(
        @classmethod
        def _from_int(cls, n, size, byteorder, signed):
            if not signed and n < 0:
                raise OverflowError("can't convert negative int to unsigned")
            if size * 8 < n.bit_length() + signed:
                raise OverflowError("int too big to convert")

            if signed and n < 0:
                n += (1 << (size * 8))

            bl = cls(size)

            if byteorder == 'little':
                it = range(size)
            else:
                it = range(size - 1, -1, -1)

            for i in it:
                bl[i] = n & 0xff
                n >>= 8
            return bl

        def _to_int(self, byteorder, signed):
            bl = self[::]
            if byteorder == 'little':
                bl.reverse()

            val = long(0)
            for b in bl:
                val <<= 8
                val |= b

            if signed:
                bl = (val.bit_length() + 7) / 8 * 8
                if val & (1 << (bl - 1)):
                    return -((1 << bl) - val)

            return val

    @classmethod
    def from_int(cls, n, size=None, byteorder='little', signed=False):
        """
        buf.from_int(n[, size[, byteorder='little'[, signed=False]]])

        Convert an integer to a byte array.
        The optional size arguemnt determines the size of the resulting array
        (By default the size is the minimum possible).
        This function is made to be behaviorally compatible with Python 3's int.to_bytes.

        >>> buf.from_int(0x1234)
        buf(hex='3412')
        >>> buf.from_int(1, 4, 'big')
        buf(hex='00000001')
        """
        if size is None:
            bl = max(n.bit_length(), 1) + bool(signed)
            size = (bl + 7) // 8
        return cls._from_int(n, size, byteorder, signed)

    def to_int(self, byteorder='little', signed=False):
        """
        b.toint([byteorder='little'[, signed=False]])

        Convert bytes to integer.
        This function is made to be behaviorally compatible with Python 3's int.from_bytes.

        >>> buf(hex='1234').to_int() == 0x3412
        True
        >>> buf(hex='ffffffff').to_int(signed=False) == 0xffffffff
        True
        >>> buf(hex='ffffffff').to_int(signed=True) == -1
        True
        """
        return self._to_int(byteorder, signed)


    def __long__(self):
        """ long(b) <==> b.__long__() <==> b.to_int()"""
        return self.to_int()

    def __int__(self):
        """ int(b) <==> b.__int__() <==> b.to_int()"""
        return self.to_int()

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

    def __unicode__(self):
        return self.decode("ascii")

    def hexdump(self, *args, **kwargs):
        """
        b.hexdump([hexdump_params])

        Return a HexDump object of the buf

        >>> b = buf(hex='68656c6c6f20776f726c64211337abcd')
        >>> print(b.hexdump())
        000000| 6865 6c6c 6f20 776f  726c 6421 1337 abcd |hello world!.7..|
        """
        return HexDump(self, *args, **kwargs)

    @classmethod
    def random(cls, size):
        """
        buf.random(size) -> buf

        Returns a randomized buf of the given size.
        >>> x = buf.random(1024)
        >>> print(len(x))
        1024
        >>> # This test isn't deterministic but is very likely and a good measure of uniformity
        >>> all(x.count(b) < 20 for b in range(256))
        True
        """
        return cls(urandom(size))

    def at(self, offset, length=1):
        """b.at(offset, length=1) <==> b[offset:offset + length]"""
        res = self[offset:offset + length]
        if len(res) != length:
            raise OverflowError("not enough data in buffer")

    def blocks(self, blocksize, padding=None):
        """
        b.blocks(blocksize[, padding]) -> iterable_of_bufs
    
        Split up the byte array into evenly-sized chunks.
        Returns a generator of blocks, each one with the specified blocksize,
        optionally right-padded with the specified padding.
        If padding is None or unspecified, length will be checked to ensure
        it is evenly divided by the blocksize. A ValueError will be raised
        otherwise. 
        If padding is not None, the last block (if partial) will be
        padded with the specified padding bytestring (use empty to disable).

        >>> g = buf(b'aaaabbbbccccdd').blocks(4)
        Traceback (most recent call last):
          ...
        ValueError: bytearray not evenly divided into blocks of size 4

        >>> for x in buf(b'aaaabbbbccccdd').blocks(4, b''):
        ...    print(x)
        aaaa
        bbbb
        cccc
        dd

        >>> for x in buf(b'something completely different').blocks(8, b'x'):
        ...    print(x)
        somethin
        g comple
        tely dif
        ferentxx
        """
        if blocksize <= 0:
            raise ValueError("invalid block size: %r" % blocksize)
        if padding is None and len(self) % blocksize != 0:
            raise ValueError("bytearray not evenly divided into blocks of size %r" % blocksize)
        return (self[i:i+blocksize].rpad(blocksize, padding) for i in range(0, len(self), blocksize))

    def unpack(self, fmt, offset=None):
        """
        b.unpack(fmt[, offset]) -> tuple

        Unpack binary values according to fmt, optionally starting from offset.

        >>> b = buf(hex="12345678abcd")
        >>> print(b.unpack('<HHH'))
        (13330, 30806, 52651)
        >>> b.unpack('<L', 2) == (3450566742,)
        True
        """
        if offset is None:
            return struct.unpack(fmt, buffer(self))
        else:
            return struct.unpack_from(fmt, self, offset)

    @classmethod
    def pack(cls, fmt, *values):
        """
        b.pack(fmt, values...) -> buf

        Pack values into a new buf accroding to fmt.

        >>> b = buf.pack('>L', 0xdeadbeef)
        >>> b.hex() == "deadbeef"
        True
        >>> print(buf.pack('5c', b'h', b'e', b'l', b'l', b'o'))
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
        >>> s = b.fields("x: u32  y: u32b  z: Bytes[4]")
        >>> s.x == 0xefbeadde
        True
        >>> s.z == buf(hex='01234567')
        True
        >>> s.y = 0xcafebabe
        >>> print(b.hex())
        deadbeefcafebabe01234567
        >>> b.fields("u16b", 2)[0] = 0xd00d
        >>> print(b.hex())
        deadd00dcafebabe01234567
        """

        from rupy import fields
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

    @classmethod
    def from_file(cls, fobj_or_filename, length=None, offset=0):
        """
        buf.fromfile(fobj_or_filename[, length[, offset=0]]) -> buf

        Read data from file or file-like object into a new buf.

        >>> f = io.BytesIO(b"Norwegian Blue")
        >>> print(buf.from_file(f, 9))
        Norwegian
        >>> _ = f.seek(0, 0)
        >>> print(buf.from_file(f, offset=10))
        Blue
        """
        if hasattr(fobj_or_filename, 'read') or hasattr(fobj_or_filename, 'readinto'):
            fobj = fobj_or_filename
            if isinstance(fobj, file):
                # default file object's readinto() is bad, m'kay?
                fobj = io.open(fobj.fileno(), getattr(fobj, "mode", "rb"))
        else:
            fobj = io.open(fobj_or_filename, 'rb')
        fobj.seek(offset, 1)
        if hasattr(fobj, 'readinto'):
            # read inplace if possible
            if length is None:
                pos = fobj.tell()
                fobj.seek(0, 2)
                length = fobj.tell() - pos
                fobj.seek(pos, 0)
            result = cls(length)
            amount_read = fobj.readinto(result)
            result[amount_read:] = []
            return result
        else:
            return cls(fobj.read(length))


    def to_file(self, fobj_or_filename, offset=None):
        """
        buf.tofile(fobj_or_filename[, offset])

        Write the buf contents to a file or file-like object.
        If a file-like object is given and offset is not None, the object's seek() method will be called.
        If a filename is given:
            - If offset is not specified or None, an existing file will be replaced;
            - Otherwise, the file will be opened for updating and contents at the specified offset
              will be overwritten in-place.

        If offset is negative it is counted from the end of the file.
        If offset is set to "append", the contents will be appended to the end of the file.

        >>> f = io.BytesIO()
        >>> b = buf(b"hello world")
        >>> b.to_file(f)
        >>> f.getvalue() == b'hello world'
        True
        >>> _ = f.seek(0, 0)
        >>> buf(b"Python").to_file(f, 6)
        >>> f.getvalue() == b'hello Python'
        True
        """
        if hasattr(fobj_or_filename, 'write'):
            fobj = fobj_or_filename
        else:
            if offset is None:
                fobj = open(fobj_or_filename, 'wb')
            else:
                fobj = open(fobj_or_filename, 'rb+')
        if offset is not None:
            if offset == 'append':
                fobj.seek(0, 2)
            elif offset < 0:
                # Seek from EOF
                fobj.seek(offset, 2)
            else:
                fobj.seek(offset, 1)
        fobj.write(self)

    def __hash__(self):
        return hash(bytes(self))

    def to_stream(self):
        """
        b.to_stream() -> BufStream

        Return a memory stream backed by this instance.
        Modifications to the stream will be reflected in the buffer and vice versa.

        >>> import io
        >>> b = buf(b"the cat goes")
        >>> s = b.to_stream()
        >>> s.read() == b'the cat goes'
        True
        >>> _=s.seek(0, io.SEEK_END)
        >>> _=s.write(b" meow")
        >>> b == b'the cat goes meow'
        True
        >>> _=s.seek(-4, io.SEEK_END)
        >>> _=s.write(b"moo")
        >>> _=s.truncate()
        >>> _=s.seek(4)
        >>> _=s.write(b"cow")
        >>> b == b'the cow goes moo'
        True
        """
        from rupy.stream import BufStream
        return BufStream(self)
