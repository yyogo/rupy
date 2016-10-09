import re
import string
import binascii
from rupy.bitview import BitView
import itertools

from rupy.hexdump import HexDump


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
        B.rpad(width[, fillchar]) -> copy of B

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
        B.lpad(width[, fillchar]) -> copy of B

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
            return "{}(hex=b'{}')".format(self.__class__.__name__, self.tohex())


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

        self.pos = 0

    def __call__(self, amount, offset=0):
        """
        x(amount, offset=0) -> buf(amount)

        Read exactly `amount` bytes from the buf at the current position.
        Increments the internal pointer.
        """
        result = self[self.pos + offset:self.pos + offset + amount]
        if len(result) != amount:
            raise OverflowError("Not enough data in buffer")
        self.pos = self.pos + offset + amount
        return result

    def __hex__(self):
        return self.tohex()

    def tohex(self):
        return binascii.hexlify(self)

    def issimpleascii(self):
        """
        b.issimpleascii() -> bool

        Returns True if b is composed of regular printable single-width characters.
        """
        return not self.translate(bytearray(range(256)), bytearray(range(32, 126)))

    def isprintable(self):
        return not self.translate(bytearray(range(256)), string.printable)


    def toint(self, little_endian=True, signed=False):
        """
        b.toint([little_endian=True[, signed=True]])

        Convert bytes to integer.
        This function is made to be behaviorally compatible with Python 3's int.from_bytes.
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
            it = range(size - 1, -1, -1)
        else:
            it = range(size)

        for i in it:
            bl[i] = n & 0xff
            n >>= 8
        return bl

    def __long__(self):
        return self.toint()

    def __int__(self):
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
        return HexDump(self, *args, **kwargs)

    @classmethod
    def random(cls, size=None):
        """
        buf.random(size) -> buf

        Returns a randomized buf of the given size.
        """
        try:
            import os
            return cls(os.urandom(size))
        except ImportError:
            import random
            return cls(random.randrange(256) for i in xrange(size))

    def at(self, offset, length=1):
        """b.at(offset, length=1) <==> b[offset:offset + length]"""
        return self[offset:offset + length]

    def blocks(self, blocksize, fillchar=None):
        """
        b.blocks(blocksize[, padding=None]) -> iterable_of_bufs

        Returns a generator of blocks, each one with the specified blocksize,
        optionally right-padded with the specified fillchar.
        """
        if fillchar is None:
            return (self[i:i+blocksize] for i in xrange(0, len(self), blocksize))
        else:
            return (self[i:i+blocksize].rpad(blocksize, fillchar) for i in xrange(0, len(self), blocksize))

    def fields(self, fieldspec, offset=0, strict=False):
        """
        b.fields(fieldspec[, offset[, strict=False]]) -> BoundFieldMap

        Create a field mapping of the buf instance with the specified field spec.
        **NOTE**: Upon creating a bound field mapping, the buffer's size cannot change as long as it is referenced
        by it.

        TODO - Document this function
        If strict is True, total sizes must match.

        >>> s = b.fields("x:uint32  y:uint32  z:Bytes(4)")
        >>> s.x
        4321
        >>> s.y = 1234

        >>> b.fields("int32", 1024)[0] = 12
        """

        from rupy import fields
        if isinstance(fieldspec, str):
            # convenience, allows writing stuff like "a:int32 b:int64 c:Bytes(16)" etc.
            #TODO Improve this silly DSL to support nested stuff
            fieldspec = [tuple(x.split(':',1)) if ':' in x else x for x in fieldspec.split()]

        map = fields.FieldMap(fieldspec)
        data = memoryview(self)[offset:offset + map.size]
        if strict and len(data) != map.size:
            raise ValueError("Field map size mismatch (and 'strict' is True)")
        return map.unpack(data)

    @property
    def bits(self):
        return BitView(self)

