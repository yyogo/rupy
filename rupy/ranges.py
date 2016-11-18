"""
Enhanced ranges

Defines a new extra-sugary Range class.

Usage examples:
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
<Range[2, 4, ..., 10]>

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
            # Series expansion
            if len(item) == 0 or item.count(Ellipsis) > 1:
                raise ValueError("Invalid series definition")
            if Ellipsis not in item:
                # explicit series, this is here for completeness sake
                start = item[0]
                if len(item) == 1:
                    return cls(start, start+1, 1)
                step = item[1] - start
                stop = item[-1] + step
                res = cls(start, stop, step)
                if list(item) != list(res):
                    raise ValueError("Invalid series")
                return res
            # series expansion
            begin, end = item[:item.index(Ellipsis)], item[item.index(Ellipsis)+1:]
            if len(begin) == 0:
                raise ValueError("Range must have lower bound")

            if len(begin) == 1:
                start, = begin
                step = 1
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
            raise IndexError(item)


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
    >>> Range[1,2,...,100][1:20:2] == Range[2,4,...,20]
    True
    >>> Range[2,4,6,...] * 2 == Range[4,8,12,...]
    True
    """

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
        self.start = start = start if start is not None else 0
        self.step = step = step if step is not None else 1
        self.stop = stop
        if step == 0:
            raise ValueError("Invalid step value")
        if stop is not None:
            if step > 0:
                self.stop = max(stop, start)
            else:
                self.stop = min(stop, start)
            if len(self) > 0:
                self.stop = self[-1] + self.step


    def _get(self, idx):
        return self.start + self.step * idx

    def __len__(self):
        if self.stop is None:
            raise TypeError("Unbounded range has no length")
        d, m = divmod(self.stop - self.start, self.step)
        return d + (1 if m != 0 else 0)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._subslice(item.start, item.stop, item.step)
        else:
            if self.stop is not None:
                if item < 0:
                    item += len(self)
                if item > len(self):
                    raise IndexError(item)
            if item < 0:
                raise IndexError(item)
            return self._get(item)

    def __contains__(self, item):
        off = (item - self.start)
        return off == 0 or \
               off % self.step == 0 and ((off > 0) == (self.step > 0)) and \
               ((self.stop is None) or (min(self.start, self[-1]) <= item <= max(self[-1], self.start)))

    def __iter__(self):
        try:
            return iter(self.as_range())
        except (OverflowError, TypeError):
            it = itertools.count(self.start, self.step)
            if self.stop is not None:
                it = itertools.islice(it, len(self))
            return it

    def __repr__(self):
        if self.stop is None:
            return '<Range[{}, {}, {}, ...]>'.format(self[0], self[1], self[2])
        elif len(self) > 4:
            return '<Range[{}, {}, ..., {}]>'.format(self[0], self[1], self[-1])
        else:
            return '<Range{}>'.format(list(self))

    def index(self, value):
        if value not in self:
            raise IndexError(value)
        return (value - self.start) // self.step

    def __reversed__(self):
        return self[::-1]

    def __eq__(self, other):
        return (self.start, self.stop, self.step) == (other.start, other.stop, other.step)

    def _subslice(self, start, stop, step):
        if step is None: step = 1
        if step < 0:
            if start is None:
                start = -1
            step *= self.step
            start = self[start]
            if stop is None:
                stop = self[0] - self.step
        else:
            step *= self.step
            start = self[start] if start is not None else self.start
            if stop is None:
                stop = self.stop
            else:
                stop = self[stop]
        return Range(start, stop, step)

    def __mul__(self, amount):
        return Range(self.start * amount, self.stop * amount if self.stop is not None else None, self.step * amount)

    def __add__(self, amount):
        return Range(self.start + amount, self.stop + amount if self.stop is not None else None, self.step)

    def as_slice(self):
        return slice(self.start, self.stop, self.step)

    def as_range(self):
        """
        Convert to native range(). If the range is unbounded, raises TypeError.

        Note: may fail on Python < 3 with OverflowError if parameters are too large.
        """
        return range(self.start, self.stop, self.step)

    def slice(self, obj):
        return obj[self.as_slice()]


__all__ = ["Range"]

if __name__ == '__main__':
    print(Range[1,2,...,10])
    print(Range[1,3,...,81])
    print(Range[0,1,...,10][::-1])
    print(Range[0,1,...,10][::-2])
    print(Range[0,1,...,10][::-3])
    print(Range[1,3,...,81][::-3])
    print(Range[0,...])
    print(list(Range[2,4,6,...,22,24]))



