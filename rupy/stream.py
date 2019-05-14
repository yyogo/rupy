from rupy.compat import *
from rupy.ranges import Range
from rupy.fields import FieldMap
import contextlib
import io


@compatible
class BufStream(io.IOBase):
    """ Like io.BytesIO, but using an external buffer. """

    def __init__(self, buffer):
        self.__buffer__ = buffer
        m = memoryview(buffer)
        self.readonly = m.readonly
        self.mode = 'rb' if self.readonly else 'rb+'
        del m  # when the memoryview is held the buffer can't be resized
        self.pos = 0
        self.name = '<buffer_%#x>' % id(buffer)

    def __len__(self):
        return len(self.__buffer__)

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    @property
    def size(self):
        return len(self)

    def _sync(self):
        self.pos = min(max(0, self.pos), len(self.__buffer__))

    def seek(self, where, whence=io.SEEK_SET):
        if whence == io.SEEK_CUR:
            where += self.pos
        elif whence == io.SEEK_END:
            where += len(self)
        where = min(len(self), where)

        self.pos = where
        return self.pos

    def write(self, data):
        if not self.writeable():
            raise IOError("buffer is not writeable")
        self._sync()
        self.__buffer__[self.pos:self.pos+len(data)] = data
        self.pos += len(data)
        return len(data)

    def read(self, amount=None):
        self._sync()
        if amount is not None:
            res = self.__buffer__[self.pos:self.pos+amount]
        else:
            res = self.__buffer__[self.pos:]
        self.pos += len(res)
        return bytes(res)

    def readinto(self, b):
        self._sync()
        amount = max(0, min(len(b), len(self.__buffer__)) - self.pos)
        b[:amount] = memoryview(self.__buffer__[self.pos:self.pos + amount])
        return amount

    def tell(self):
        self._sync()
        return self.pos

    def truncate(self, size=None):
        self._sync()
        if size is None:
            size = self.pos
            self.__buffer__[size:] = ()
            return len(self.__buffer__)

    def close(self):
        self.__buffer__ = None
        super(BufStream, self).close()

    def readable(self):
        return True
    def writeable(self):
        return not self.readonly
    def seekable(self):
        return True
    def isatty(self):
        return False

    def __next__(self):
        s = self.readline()
        if s:
            return s
        else:
            raise StopIteration

    def getbuffer(self):
        return self.__buffer__

    def getvalue(self):
        return bytes(self.__buffer__)


@compatible
class Stream(io.IOBase):
    """
    Stream(filelike_object [,start=0 [, stop]])
    Stream.open(filename [,mode, start, stop, ...]) => Stream(io.open(filename, mode, ...), start, stop)

    An enhanced binary IO stream with slicing support. Does not support resizing streams.
    TODO come up with a better name.
    """
    DEFAULT_BLOCKSIZE = 4*1024*1024  # 4Mb

    def __init__(self, stream, start=0, stop=None):
        super(Stream, self).__init__()
        if isinstance(stream, file):
            # default file object's readinto() is bad, m'kay?
            stream = io.open(stream.fileno(), "rb", buffering=0) 

        if 'b' not in stream.mode or getattr(stream, 'encoding', None) is not None:
            raise ValueError("Stream only works with binary streams")

        self.mode = stream.mode
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

    def __enter__(self):
        return self

    @classmethod
    def open(cls, filename, mode='rb', start=0, stop=None, **kwargs):
        """ Stream.open(filename [, mode, start, stop, ...]) => Stream(io.open(filename, mode, ...), start, stop) """
        return cls(io.open(filename, mode, **kwargs), start=start, stop=stop)

    def close(self):
        self.__stream__ = None
        super(Stream, self).close()

    @classmethod
    def from_bytes(cls, bytes=b'', start=0, stop=None):
        return cls(io.BytesIO(bytes), start=start, stop=stop)

    @classmethod
    def from_buffer(cls, buffer, start=0, stop=None):
        return cls(BufStream(buffer), start=start, stop=stop)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if idx.step not in (1, None):
                raise ValueError("Stream doesn't support non-sequential slices")
            start, stop = idx.start if idx.start is not None else 0, idx.stop if idx.stop is not None else self.stop
            start += self.start
            if stop is not None:
                stop = max(start, min(self.start + stop, self.stop))
            return Stream(self.__stream__, start, stop)

        return bytes(self[idx:idx+1])[0]

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
        """ This may fail on Python 2 if the file size is larger than INT_MAX."""
        if self.size is None:
            raise IOError("Stream has no defined length")
        return self.size

    def __repr__(self):
        return "<{self.__class__.__name__} [{self.start}:{self.stop}] of {self.name!r}>".format(self=self)

    def __bytes__(self):
        with self.at(0):
            return self.read()

    def __iter__(self):
        buf = bytearray(self.DEFAULT_BLOCKSIZE)
        for _ in self.buffer(buf):
            for x in buf:
                yield x

    def blocks(self, blocksize=DEFAULT_BLOCKSIZE, tail=0):
        """ stream.blocks([blocksize [,tail]]) => generator of Streams

        Iterate over stream blocks with the specified blocksize.
        Yields stream slices.
        """
        for i in Range(0, self.size, blocksize):
            b = (self[i:i + blocksize + tail])
            yield b

    def buffer(self, buf, tail=0):
        """ stream.buffer(buffer_object [,tail=0]) => coroutine yielding ints

        Iterate over blocks with an external buffer. Yields starting offset for each block. 
        Will truncate the buffer on incomplete read.
        The optional tail argument makes the buffer contain some data from the beginning
        of the next block (useful for e.g searches).
        """
        for b in self.blocks(len(buf) - tail, tail):
            r = b.readinto(buf)
            if r < len(buf):
                # truncate buffer
                buf[r:] = buf[:0]
            yield b.start

    def ifind(self, value, blocksize=DEFAULT_BLOCKSIZE):
        while len(value) > blocksize:
            blocksize *= 2
        buf = bytearray(blocksize)
        for i in self.buffer(buf, len(value)):
            x = buf.find(value)
            while x >= 0:
                yield i + x
                x = buf.find(value, x + 1)

    def __contains__(self, item):
        for i in self.ifind(item):
            return True
        return False

    def _sync(self):
        try:
            self.__stream__.seek(self._ptr + self.start, io.SEEK_SET)
        except IOError:
            # can't seek
            self.seekable = lambda: False

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

    def read_full(self, amount):
        """ Read the specified amount of bytes; if not enough in stream, fail (and leave stream unchanged). """
        data = self.read(amount)
        if len(data) != amount:
            self.seek(-amount, io.SEEK_CUR)
            raise IOError("Incomplete read (requested %d bytes, got %d)" % (amount, len(data)))
        return data

    def readall(self):
        return self.read(-1)

    def readinto(self, obj):
        if self.size is not None:
            obj = memoryview(obj)[:min(len(obj), self.size - self._ptr)]
        self._sync()
        if hasattr(self.__stream__, "readinto"):
            return self.__stream__.readinto(obj)
        else:
            data = self.__stream__.read(len(obj))
            obj[:len(data)] = data

    def readat(self, offset, amount=-1):
        with self.at(offset, io.SEEK_SET):
            return self.read(amount)

    def getbuffer(self):
        """ Returns a buffer object containing the stream data. """
        if hasattr(self.__stream__, "getbuffer"):
            return self.stream.getbuffer()
        return self.getvalue()

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
        if not self.seekable():
            raise IOError("Can't seek")
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
        for _ in self.icopy(stream, blocksize):
            pass # Already done

    def icopy(self, stream, blocksize=DEFAULT_BLOCKSIZE):
        """
        Copy data to another stream. Returns a generator yielding current offset.

        :param stream: The stream to copy data to
        :param blocksize: Optional; transfer block size.
        :return: a generator
        """
        buf = bytearray(blocksize)
        for i in self.buffer(buf):
            yield i
            stream.write(buf)
        yield self.size

    def fields(self, fieldspec):
        """
        stream.fields(fieldspec) -> BoundFieldMap

        Parse fields directly from the stream. Changes to the returned
        instance are not written back to the stream.

        >>> b = bytearray.fromhex("deadbeef0000010000010000aabbccdd")
        >>> stream = Stream.from_buffer(b)
        >>> fields = stream.fields('x: u16b  y: u16b z: u32l')
        >>> print('x: {f.x:x} y: {f.y:x} z: {f.z:x}'.format(f=fields))
        x: dead y: beef z: 10000
        """
        fm = FieldMap(fieldspec)
        data = bytearray(self.read_full(fm.size))
        return fm.unpack(data)
