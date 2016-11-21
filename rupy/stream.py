from rupy.compat import *
from rupy.ranges import Range
from rupy.buf import buf

import contextlib
import io

@compatible
class Stream(io.IOBase):
    DEFAULT_BLOCKSIZE = 4*1024*1024  # 4Mb

    def __init__(self, stream, start=0, stop=None):
        super(Stream, self).__init__()
        if isinstance(stream, file):
            # default file object's readinto() is bad, m'kay?
            stream = io.open(stream.fileno(), getattr(stream, "mode", "rb"), buffering=0)

        self.__stream__ = stream

        size = getattr(stream, 'size', None)
        if size is None:
            try:
                tmp = stream.tell()
                stream.seek(0, io.SEEK_END)
                size = stream.tell()
                stream.seek(tmp, io.SEEK_SET)
            except:
                pass
        self.name = getattr(stream, "name", repr(stream))

        start = max(start, 0)

        if size is not None:
            start = min(start, size)
            if stop is not None:
                stop = min(max(stop, start), size)
            else:
                stop = size
            size = stop - start

        self.start = start
        self.size = size
        self.stop = stop

        self._ptr = 0

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if idx.step not in (1, None):
                raise ValueError("Can't have stream slice with step value")
            start, stop = idx.start if idx.start is not None else 0, idx.stop if idx.stop is not None else self.stop
            start += self.start
            if stop is not None:
                stop = max(start, min(self.start + stop, self.stop))
            return Stream(self.__stream__, start, stop)

        return bytes(self[idx:idx+1])

    def __setitem__(self, idx, value):
        if not isinstance(idx, slice):
            idx = slice(idx, idx+1)
        s = self[idx]
        if s.size is not None and s.size != len(value):
            raise OverflowError("Unmatched stream size")
        if isinstance(value, Stream):
            value.copy(s)
        else:
            s.write(value)

    def __len__(self):
        if self.size is None:
            raise IOError("Stream has no defined length")
        return self.size

    def __repr__(self):
        return "<StreamSlice [{self.start}:{self.stop}] of {self.name!r}>".format(self=self)

    def __bytes__(self):
        with self.at(0):
            return self.read()

    def __iter__(self):
        for i, b in self.blocks(self.DEFAULT_BLOCKSIZE):
            for x in b:
                yield x

    def blocks(self, blocksize=DEFAULT_BLOCKSIZE, tail=0):
        buf = bytearray(blocksize + tail)
        for i in Range(0, self.size, blocksize):
            b = (self[i:i + blocksize + tail])
            r = b.readinto(buf)
            if r < blocksize + tail:
                yield i, buf[:r]
                break
            else:
                yield i, buf

    def ifind(self, value, blocksize=DEFAULT_BLOCKSIZE):
        for i, b in self.blocks(blocksize, len(value)):
            x = b.find(value)
            while x >= 0:
                yield i + x
                x = b.find(value, x + 1)

    def __contains__(self, item):
        for i in self.ifind(item):
            return True
        return False

    def _sync(self):
        self.__stream__.seek(self._ptr + self.start, io.SEEK_SET)

    @contextlib.contextmanager
    def at(self, where, whence=io.SEEK_SET):
        tmp = self._ptr
        o = self.seek(where, whence)
        try:
            yield o
        finally:
            self.seek(tmp, io.SEEK_SET)

    def read(self, amount=None):
        if amount is None or amount < 0:
            amount = self.size
        if self.size is not None:
            amount = max(0, min(int(amount), self.size - self._ptr))
        elif amount is None:
            amount = -1
        self._sync()
        res = self.__stream__.read(amount)
        self._ptr += len(res)
        return res

    def readall(self):
        return self.read(-1)

    def readinto(self, obj):
        if self.size is not None:
            obj = memoryview(obj)[:min(len(obj), self.size - self._ptr)]
        self._sync()
        return self.__stream__.readinto(obj)

    def readat(self, offset, amount=-1):
        with self.at(offset, io.SEEK_SET):
            return self.read(amount)

    def getbuffer(self):
        if hasattr(self.__stream__, "getbuffer"):
            return self.stream.getbuffer()
        if self.size is None:
            raise ValueError("Can't get stream buffer; stream has no size")
        b = buf(self.size)
        with self.at(0):
            self.readinto(b)
        return b

    def getvalue(self):
        if hasattr(self.__stream__, "getvalue"):
            return self.stream.getvalue()
        return self.__bytes__()

    def write(self, data):
        if self.size is not None and len(data) > self.size - self._ptr:
            data = memoryview(data)[:self.size - self._ptr]
        self._sync()
        return self.__stream__.write(data)

    def writeat(self, offset, data):
        with self.at(offset, io.SEEK_SET):
            return self.write(data)

    def seek(self, where, whence=io.SEEK_SET):
        if whence == io.SEEK_CUR:
            where += self._ptr
        elif whence == io.SEEK_END:
            if self.size is None:
                raise IOError("Invalid seek argument")
            where += self.size

        if self.size is not None:
            where = min(self.size, where)

        self._ptr = where
        return self._ptr

    def tell(self):
        return self._ptr

    def readable(self):
        return getattr(self.__stream__, 'readable', lambda : False)()

    def writeable(self):
        return getattr(self.__stream__, 'writeable', lambda : False)()

    def seekable(self, *args, **kwargs):
        return getattr(self.__stream__, 'seekable', lambda: False)()

    def isatty(self, *args, **kwargs):
        return getattr(self.__stream__, 'isatty', lambda: False)()

    def copy(self, stream, blocksize=DEFAULT_BLOCKSIZE):
        """
        Copy data to another stream.

        :param stream: The stream to copy data to
        :param blocksize: Optional; transfer block size.
        :return: None
        """
        for i in self.icopy(stream, blocksize):
            pass # Already done

    def icopy(self, stream, blocksize=DEFAULT_BLOCKSIZE):
        """
        Copy data to another stream. Returns a generator yielding current offset.

        :param stream: The stream to copy data to
        :param blocksize: Optional; transfer block size.
        :return: a generator
        """
        for i, b in self.blocks(blocksize):
            yield i
            stream.write(b)
        yield self.size
