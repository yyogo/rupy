import itertools
from rupy.ranges import Range
from rupy.compat import *


@compatible
class BitView(object):
    def __init__(self, obj, start=None, stop=None, step=None):
        self.__buffer__ = obj
        self._range = Range(start, stop, step).clamp(len(obj) * 8 - 1)

    def copy(self):
        """
        bv.copy() => bitview instance (with new buffer)

        Copy the bit view and the associated data (only within the slice).
        """
        from rupy import buf
        n = self.to_int()
        n <<= (-len(self)) % 8  # pad *bottom* with zeroes
        b = buf.from_int(n, size=(len(self) + 7) // 8, byteorder='big')
        return self.__class__(b, stop=len(self))

    def _get(self, idx):
        return (self.__buffer__[idx // 8] >> ((idx ^ 7) & 7)) & 1

    def _set(self, idx, value):
        idx ^= 7
        b = self.__buffer__[idx // 8] & (~(1 << (idx & 7)))
        self.__buffer__[idx // 8] = b | (bool(value) << (idx & 7))

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._subslice(item)
        elif isinstance(item, (int, long)):
            idx = self._range[item]
            return self._get(idx)
        else:
            raise TypeError("indices must be integers or slices")

    def __setitem__(self, item, value):
        if isinstance(item, slice):
            sub = self._subslice(item)
            sub.apply(value)
        elif isinstance(item, (int, long)):
            idx = self._range[item]
            self._set(idx, value)
        else:
            raise TypeError("indices must be integers or slices")

    def __len__(self):
        return len(self._range)

    def __iter__(self):
        for i in self._range:
            yield self._get(i)

    def __str__(self):
        """ x.__str__() <=> str(x) """
        # Return string (rather than bytes) in both Python 2 and 3
        # so you can just "print b.bits"
        return ''.join(('0', '1')[x] for x in self)

    def __format__(self, spec):
        """
        bv.__format__(spec) <=> format(bv, spec) 

        format the bits according to the spec.
        Spec can be an array of comma-seperated integers, indicating the grouping of the bits.
        Use negative values to reverse the group.
        e.g, a spec of '4' will group by 4 bits; '8,2' will group by 8 bits, then by 2 groups of 8.
        groups are seperated by spaces by default. You may specify an alternative character by
        a semicolon at the end of the spec, e.g: "4,2;-" will use "-" as a seperator.
        """

        # this could probably be written better. meh
        if spec:
            try:
                spec_fields = spec.split(';', 1)
                seperator = ' '
                if len(spec_fields) > 1:
                    seperator = spec_fields[1]
                spec = spec_fields[0]
                groups = [int(x) for x in spec.split(',')]
                out = self
                for g in groups:
                    if g == 0:
                        raise ValueError()
                    sgn = 1 if g > 0 else -1
                    g *= sgn
                    out = [out[i:i+g][::sgn] for i in range(0, len(out), g)]
                def _flatten(m):
                    if isinstance(m, list):
                        return seperator.join(_flatten(x) for x in m) + seperator
                    return str(m)
                return _flatten(out).strip()
            except ValueError:
                raise ValueError("Invalid format specification")
        else:
            return str(self)

    def __bytes__(self):
        """ x.__bytes__() <=> bytes(x)  # in Python 3.x """
        return bytes(self.to_bytes())

    def __repr__(self):
        if len(self) > 64:
            b = u'...'.join((str(self[:48]), str(self[-10:])))
        else:
            b = str(self)
        return '<BitView(<%s>, %s) |%s|>' % (
                self.__buffer__.__class__.__name__, self._range, b)

    def __nonzero__(self):
        return any(x for x in self)

    def __ixor__(self, other):
        for i, x in zip(self._range, other):
            self[i] ^= x
        return self

    def __iand__(self, other):
        for i, x in zip(self._range, other):
            self[i] &= x
        return self

    def __ior__(self, other):
        for i, x in  zip(self._range, other):
            self[i] |= x
        return self

    def __irshift__(self, amount):
        self.shift_right(amount)

    def __ilshift__(self, amount):
        self.shift_left(amount)

    def shift_right(self, amount):
        self.apply([0] * amount + list(self))

    def shift_left(self, amount):
        self.apply(itertools.chain(self[amount:], [0] * amount))

    def rotate_right(self, amount):
        self.apply(list(self[-amount:]) + list(self[:-amount]))

    def rotate_left(self, amount):
        self.apply(list(self[amount:]) + list(self[:amount]))

    def invert(self):
        """
        Invert each bit in the range
        """
        self.__ixor__(itertools.cycle([1]))

    def set(self, index=None):
        if index is None:
            for i in self._range:
                self._set(i, 1)
        else:
            self._set(index, 1)

    def reset(self, index=None):
        if index is None:
            for i in self._range:
                self._set(i, 0)
        else:
            self._set(index, 0)

    def apply(self, bits):
        for i, x in zip(self._range, bits):
            self._set(i, x)

    def to_int(self, msb_first=True):
        s = str(self)
        if msb_first:
            s = s[::-1]
        return int(s, 2)

    def from_int(self, n, msb_first=True):
        if n.bit_length() > len(self):
            raise OverflowError("Integer value too big to fit in bit view")
        r = self._range
        if msb_first:
            r = reversed(r)
        for i in r:
            self[i] = n & 1
            n >>= 1

    @property
    def int_lsb(self):
        """ Return the lsb-first integer value of the bits """
        return self.to_int(msb_first=False)

    @int_lsb.setter
    def int_lsb(self, n):
        self.from_int(n, msb_first=False)

    @property
    def int_msb(self):
        """ Return the (msb-first) integer value of the bits """
        return self.to_int(msb_first=True)

    @int_msb.setter
    def int_msb(self, n):
        self.from_int(n, msb_first=True)

    # bit representation - msb first by default (makes more sense)
    int = int_msb

    def to_bytes(self):
        if len(self) % 8 != 0:
            raise ValueError("Bit view not aligned to octet")
        from rupy.buf import buf
        return buf.from_int(self.to_int(), size=len(self) // 8, byteorder='big')

    def rev8(self):
        if len(self) % 8 != 0:
            raise ValueError("Bit view not aligned to octet")
        for i in range(0, len(self), 8):
             self[i:i+8].reverse()

    def reverse(self):
        """

        Reverse the bits of the buffer in-place
        """
        self[:] = list(self[::-1])

    def _subslice(self, sl):
        r = self._range[sl]
        return BitView(self.__buffer__, r.start, r.stop, r.step)

