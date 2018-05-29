"""
Range() - A saner integer range implementation
Now with extra sugar!

Range is similar to builtin range() functions, except it also supports:
    * Sub-slicing
    * Unbounded ranges
    * Series notation using ellipsis
    * Arithmetic operations on ranges
    * And much more!

All this goodness with negligible overhead, since Range() uses builtin types for the actual
iteration, such as xrange()/range() and itertools.count().

Usage examples:
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
...        print("I'm tired!")
...        break
I'm tired!

>>> print(Range[0, ...][2:12:2])
Range[2, 4, ..., 10]

Tests:

>>> Range(0, 10)
Range[0, 1, ..., 9]
>>> Range[1,2,...,10]
Range[1, 2, ..., 10]
>>> Range[1,2,...,10][:]
Range[1, 2, ..., 10]
>>> Range[1,2,...,10][:10]
Range[1, 2, ..., 10]
>>> Range[1,2,...,10][::-1]
Range[10, 9, ..., 1]
>>> Range[1,3,...,81]
Range[1, 3, ..., 81]
>>> Range[0,1,...,10][::-1]
Range[10, 9, ..., 0]
>>> Range[0,1,...,10][::-2]
Range[10, 8, ..., 0]
>>> Range[0,1,...,10][::-3]
Range[10, 7, 4, 1]
>>> Range[1,3,...,81][::-3]
Range[81, 75, ..., 3]
>>> Range[0,...]
Range[0, 1, 2, ...]
>>> -Range[0,...]
Range[0, -1, -2, ...]
>>> list(Range[2,4,6,...,22,24])
[2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
>>> Range[10, ..., 0] == Range(10, -1, -1)
True

"""
from __future__ import print_function
from rupy.compat import *
import itertools

# The metaclass is used to support indexing syntax (ugly hack but pretty results!)
class RangeMeta(type):
    def __getitem__(cls, item):
        if isinstance(item, (slice, Range)):
            start, stop, step = item.start, item.stop, item.step
            return cls(start, stop, step)
        elif isinstance(item, tuple):
            # Seqeuence expansion
            if len(item) == 0 or item.count(Ellipsis) > 1:
                raise ValueError("Invalid series definition")
            if Ellipsis not in item:
                # explicit sequence, this is here for completeness sake
                start = item[0]
                if len(item) == 1:
                    return cls(start, start+1, 1)
                step = item[1] - start
                stop = item[-1] + step
                res = cls(start, stop, step)
                if list(item) != list(res):
                    raise ValueError("Invalid series")
                return res
            # sequence expansion
            begin, end = item[:item.index(Ellipsis)], item[item.index(Ellipsis)+1:]
            if len(begin) == 0:
                raise ValueError("Range must have lower bound")

            if len(begin) == 1:
                start, = begin
                # Allow for descending sequence like [8, ..., 1]
                step = -1 if len(end) > 0 and end[-1] < start else 1
            else:
                start, sec = begin[:2]
                step = sec - start
            res = cls(start=start, step=step)

            if list(res[:len(begin)]) != list(begin):
                raise ValueError("Invalid series")

            if len(end) > 0:
                last = end[-1]
                stop = last + step
                res = res[:res.index(stop)]

                if list(end) != list(res[-len(end):]):
                    raise ValueError("Invalid series")

            return res

        else:
            raise TypeError("Can't parse series notation")


class Range(metabase(RangeMeta)):
    """
    Range([stop])
    Range(start, stop[, step])
    Range[a0, a1, ...]
    Range[a0, a1, ..., an]

    Define a range with the specified parameters.
    If stop is None or not specified, the range will be unbounded, and can be iterated indefinitely.
    You can supply either keyword or positional arguments.
    Range() <=> Range(0, None, 1) <=> Range(start=0, stop=None, step=1)

    You can use series notation to define ranges, e.g:

    >>> Range[1, 2, ..., 10] == Range(1, 11)
    True
    >>> Range[0, 3, ...] == Range(start=0, stop=None, step=3)
    True
    >>> Range[1, 2, 3, 4, 5] == Range(1, 6)
    True

    Ranges can be sliced, shifted (using addition) and "stretched" (using multiplication):
    >>> Range[1,2,...,100][1:20:2]
    Range[2, 4, ..., 20]
    >>> Range[2,4,6,...] * 2
    Range[4, 8, 12, ...]
    """
    __slots__ = ['start', 'step', 'stop']

    def __init__(self, *args, **kwargs):
        if args and kwargs:
            raise TypeError("Can supply either postitional arguments (range()-style) or keywords, not both")
        start, stop, step = None, None, None
        if args:
            if len(args) == 1:
                stop, = args
            elif len(args) == 2:
                start, stop = args
            elif len(args) == 3:
                start, stop, step = args
            elif len(args) > 3:
                raise TypeError("Range() expects up to 3 positional arguments")
        elif kwargs:
            start, stop, step = kwargs.pop('start', None), kwargs.pop('stop', None), kwargs.pop('step', None)
            if kwargs:
                raise TypeError("Range() got an unexpected keyword argument %r" % iter(kwargs.keys()).next())
        if step == 0:
            raise ValueError("Invalid step value")
        self.step = step or 1
        self.start = start or 0
        self.stop = None
        if stop is not None:
            if self.step > 0:
                stop = max(stop, self.start)
            else:
                stop = min(stop, self.start)
            stop = self._form(self._alias(stop))
        self.stop = stop

    def _form(self, idx):
        """ Apply the series function on idx. -> step * idx + start """
        return self.start + self.step * idx

    def _alias(self, value, roundup=True):
        """ Find the nearest value in the range """
        d, m = divmod(value - self.start, self.step)
        if m != 0 and roundup:
            d += 1
        return d

    def is_bounded(self):
        """
        Range.is_bounded() -> bool

        Returns True iff the range is finite, i.e has a stop value.
        """
        return self.stop is not None

    def __len__(self):
        if not self.is_bounded():
            raise TypeError("Unbounded range has no length")
        return (self.stop - self.start) // self.step

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._subslice(item)
        else:
            if self.is_bounded():
                if item < 0:
                    item += len(self)
                elif item >= len(self):
                    raise IndexError(item)
            if item < 0:
                raise IndexError(item)
            return self._form(item)

    def __contains__(self, item):
        d, m = divmod(item - self.start, self.step)
        return m == 0 and d >= 0 and (not self.is_bounded() or d < len(self))

    def __iter__(self):
        try:
            return iter(self.as_range())
        except (OverflowError, TypeError):
            it = itertools.count(self.start, self.step)
            if self.is_bounded():
                it = itertools.islice(it, len(self))
            return it

    def __repr__(self):
        if not self.is_bounded():
            return 'Range[{}, {}, {}, ...]'.format(self[0], self[1], self[2])
        elif len(self) > 4:
            return 'Range[{}, {}, ..., {}]'.format(self[0], self[1], self[-1])
        elif len(self) == 0:
            return 'Range(0)'
        else:
            return 'Range{}'.format(list(self))

    def __nonzero__(self):
        return not (self.is_bounded() and len(self) == 0)

    def __pos__(self):
        return self

    def __neg__(self):
        return self * -1

    def index(self, value):
        """
        Range.index(value)

        Return the index where value appears in the range.
        Raise IndexError if it doesn't.

        >>> Range[0, 5, ...].index(781236459815) == 156247291963
        True
        """
        d, m = divmod(value - self.start, self.step)
        if m != 0 or d < 0 or (self.is_bounded() and d > len(self)):
            raise IndexError(value)
        return int(d)

    def __reversed__(self):
        return iter(self[::-1])

    def __eq__(self, other):
        if not isinstance(other, (Range, slice)):
            return NotImplemented
        return (self.start, self.stop, self.step) == (other.start, other.stop, other.step)

    def __ne__(self, other):
        if not isinstance(other, (Range, slice)):
            return NotImplemented
        return not self == other

    def _subslice(self, sl):
        if self.is_bounded():
            # easy case
            start, stop, step = sl.indices(len(self))
            return Range(self._form(start), self._form(stop), self.step * step)
        else:
            # annyoing case
            start, stop, step = sl.start, sl.stop, sl.step
            step = step or 1
            if stop is not None and stop < 0:
                raise IndexError("Can't use negative indices with unbounded range")

            if step > 0:
                if start is None:
                    start = 0
            else:
                if start is None:
                    raise IndexError("Can't reverse unbounded range")
                if stop is None:
                    stop = -1

            rstop = self._form(stop) if stop is not None else None
            return Range(self[start], rstop, self.step * step)

    def __mul__(self, amount):
        return Range(self.start * amount, self.stop * amount if self.is_bounded() else None, self.step * amount)

    def __sub__(self, amount):
        return Range(self.start - amount, self.stop - amount if self.is_bounded() else None, self.step)

    def __add__(self, amount):
        return Range(self.start + amount, self.stop + amount if self.is_bounded() else None, self.step)

    def as_slice(self):
        """
        Range.as_slice() -> slice

        Returns a slice with the same shape as the range.

        >>> Range[3, 6, ...].as_slice()
        slice(3, None, 3)
        """
        return slice(self.start, self.stop, self.step)

    def as_range(self):
        """
        Range.as_range() -> range() (Python3.3+) / xrange() (Python2.7)

        Convert to native range(). If the range is unbounded, raises TypeError.

        Note: may fail on Python < 3 with OverflowError if parameters are too large.

        >>> r = Range[1,2,..., 20]
        >>> list(r) == list(r.as_range())
        True
        """
        return range(self.start, self.stop, self.step)

    def slice(self, obj):
        """
        Range.slice(obj) <==> obj[Range.as_slice()]
        """
        return obj[self.as_slice()]

    def clamp(self, *args):
        """
        Range.clamp([low, ]high) -> Range

        Return a Range bounded by the supplied values.
        All values in the resulting range will be in the range [low, high].

        >>> r = Range()
        >>> r
        Range[0, 1, 2, ...]
        >>> r.clamp(20)
        Range[0, 1, ..., 20]
        >>> Range[29, 28, ...].clamp(5, 10)
        Range[10, 9, ..., 5]
        >>> Range[2, 4, ..., 36].clamp(7, 19)
        Range[8, 10, ..., 18]
        >>> Range(10, 20).clamp(30, 40)
        Range(0)
        >>> Range(10, 20).clamp(5, 5)
        Range(0)
        >>> Range(10, 20).clamp(5, 15)
        Range[10, 11, ..., 15]
        >>> Range[12, 15, ..., 24].clamp(16, 17)
        Range(0)
        """
        low = 0
        if len(args) == 1:
            high, = args
        elif len(args) == 2:
            low, high = args
        else:
            raise TypeError("Range.clamp() expected 1, 2 arguments (%d given)" % len(args))

        if self.step < 0:
            high, low = low, high
        start, end = self._alias(low), self._alias(high, False)
        return self[max(0, start):max(0, end+1)]

    def indices(self, length=None):
        """
        Range.indices([length]) -> (start, stop, step)

        Like slice.indices():
        Assuming a sequence of length len, calculate the start and stop
        indices, and the stride length of the extended slice described by
        S. Out of bounds indices are clipped in a manner consistent with the
        handling of normal slices.

        >>> Range().indices(10)
        (0, 10, 1)
        >>> Range[2, 4, ..., 12].indices(30)
        (2, 14, 2)
        >>> Range[10, 9, ...].indices(6)
        (5, -1, -1)
        >>> Range[10, 8, ...].indices(6)
        (4, -2, -2)
        """
        if length is not None:
            r = self.clamp(length - 1)
        else:
            r = self
        return r.start, r.stop, r.step

__all__ = ["Range"]

if __name__ == '__main__':
    import doctest
    doctest.testmod()

