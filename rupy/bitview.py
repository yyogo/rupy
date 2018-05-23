import itertools
from rupy.compat import *
from rupy.ranges import Range


class BitView(object):
    def __init__(self, obj, start=None, stop=None, step=None):
        self.__buffer__ = obj
        self._range = Range(start, stop, step).clamp(len(obj) * 8 - 1)

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
        return bin(self.to_int())[2:].zfill(len(self))

    def __repr__(self):
        if len(self) > 64:
            b = u'...'.join([str(self[:48]), str(self[-10:])])
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

    def to_int(self, little_endian=False):
        r = self._range
        if not little_endian:
            r = reversed(r)
        return sum(self._get(x) << i for i, x in enumerate(r))

    def from_int(self, n, little_endian=False):
        r = self._range
        if not little_endian:
            r = reversed(r)
        for i in r:
            self[i] = n & 1
            n >>= 1

    def to_bytes(self):
        if len(self) % 8 != 0:
            raise ValueError("Bit view not aligned to octet")
        from rupy.buf import buf
        return buf.from_int(self.to_int(), 'little')

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

