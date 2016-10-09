import itertools

class BitView(object):
    def __init__(self, object, start=None, stop=None, step=None):
        self.object = object
        self.slice = slice(start, stop, step)
        self._range = xrange(*self.slice.indices(len(self.object) * 8))

    def _get(self, idx):
        return (self.object[idx / 8] >> (idx % 8)) & 1

    def _set(self, idx, value):
        b = self.object[idx / 8] & (~(1 << (idx % 8)))
        self.object[idx / 8] = b | (bool(value) << (idx % 8))

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
        return u''.join('01'[self._get(i)] for i in self._range)

    def __repr__(self):
        return '<BitView of %s(%d) instance (%s, %s, %s)>' % (
            type(self.object), len(self.object), self.slice.start, self.slice.stop, self.slice.step)

    def __nonzero__(self):
        return any(x != 0 for x in self)

    def __ixor__(self, other):
        for i, x in itertools.izip(self._range, other):
            self[i] ^= x
        return self

    def __iand__(self, other):
        for i, x in itertools.izip(self._range, other):
            self[i] &= x
        return self

    def __ior__(self, other):
        for i, x in itertools.izip(self._range, other):
            self[i] |= x
        return self

    def invert(self):
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
        for i, x in itertools.izip(self._range, bits):
            self._set(i, x)

    def toint(self, little_endian=False):
        r = self._range
        if not little_endian:
            r = reversed(r)
        return sum(self._get(x) << i for i, x in enumerate(r))

    def fromint(self, n, little_endian=False):
        r = self._range
        if not little_endian:
            r = reversed(r)
        for i in r:
            self[i] = n & 1
            n >>= 1

    def _subslice(self, sl):
        start, stop, step = sl.indices(len(self))
        mstart, mstop, mstep = self.slice.indices(len(self.object) * 8)
        sstart = mstart + mstep * start
        sstop = mstart + mstep * stop
        sstep = mstep * step
        if sstart < 0 and sstep > 0:
            sstart = None
        if sstop < 0 and sstep < 0:
            sstop = None
        return BitView(self.object, sstart, sstop, sstep)


