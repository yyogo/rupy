from rupy.buf import buf
import struct
import re

import operator


class BasicField(object):
    def __init__(self, fmt):
        self.st = struct.Struct(fmt)
        self.size = self.st.size

    def unpack(self, buf):
        return self.st.unpack(buf)[0]

    def pack(self, buf, data):
        self.st.pack_into(buf, 0, data)

class Bytes(object):
    buftype = buf
    def __init__(self, size):
        self.size = size

    def unpack(self, buf):
        res = self.buftype(buf[:self.size])
        if len(res) != self.size:
            raise ValueError("insufficient data in buffer for Bytes field")
        return res

    def pack(self, buf, data):
        if len(data) != self.size:
            raise ValueError('data size mismatch for Bytes field')
        buf[:self.size] = data


uint8 = byte = BasicField("<B")
int8 = char = BasicField('<b')
uint16 = uint16l = BasicField("<H")
uint32 = uint32l = BasicField("<L")
uint64 = uint64l = BasicField("<Q")
uint16b = BasicField(">H")
uint32b = BasicField(">L")
uint64b = BasicField(">Q")
int16 = int16l = BasicField("<h")
int32 = int32l = BasicField("<l")
int64 = int64l = BasicField("<q")
int16b = BasicField(">h")
int32b = BasicField(">l")
int64b = BasicField(">q")

class FieldView(object):
    _fieldset = None
    def __init__(self, buf):
        if len(buf) < self._fieldset.size:
            raise ValueError("Not enough data in buffer")
        self.__buffer__ = buf

    def __len__(self):
        return len(self._fieldset)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return tuple(self[i] for i in xrange(*item.indices(len(self))))
        return self._fieldset.get(self.__buffer__, item)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            r = xrange(key.indices(len(self)))
            if len(value) != len(r):
                raise ValueError("mismatched value count in field assignment")
            for i, x in zip(r, value):
                self._fieldset.set(self.__buffer__, i, x)
        else:
            self._fieldset.set(self.__buffer__, key, value)

class FieldSet(object):
    def __init__(self, fields):
        if len(fields) == 0:
            raise ValueError("can't create empty field set")
        self.fields = fields
        self.size = sum(x.size for x in fields)
        self.offsets = [0]
        for f in self.fields[:-1]:
            self.offsets.append(self.offsets[-1] + f.size)
        attrs = {"_fieldset": self, '__repr__': lambda self: repr(self[::])}
        self._bound = type("BoundFieldSet", (FieldView,), attrs)

    def __len__(self):
        return len(self.fields)

    def unpack(self, buf):
        return self._bound(buf)

    def pack(self, buf, values):
        if len(values) != len(self.fields):
            raise ValueError("FieldSet.pack(): incorrect value count")
        for i, v in enumerate(values):
            self.set(buf, i, v)

    def set(self, buf, index, value):
        f = self.fields[index]
        offset = self.offsets[index]
        f.pack(memoryview(buf)[offset:offset + f.size], value)

    def get(self, buf, index):
        f = self.fields[index]
        offset = self.offsets[index]
        return f.unpack(memoryview(buf)[offset:offset + f.size])

def Array(field, count):
    return FieldSet([field] * count)

def getter(i):
    return lambda x: x[i]

def setter(i):
    return lambda x, v: operator.setitem(x, i, v)


def parse_field_spec(s):

    if s in globals():
        return globals()[s]
    m = re.match(r'(\w+)\(([0-9]+)\)', s)
    if m:
        name, value = m.groups()
        return globals()[name](int(value))
    m = re.match(r'(\w+)\[([0-9]+)\]', s)
    if m:
        name, value = m.groups()
        return Array(globals()[name], int(value))
    raise ValueError("Invalid field specification")


class FieldMap(FieldSet):
    """
    DOCME
    """
    def __init__(self, fieldspec):
        fields = []
        names = {}
        name_l = []
        properties = {}

        for i, v in enumerate(fieldspec):
            if isinstance(v, tuple):
                k, v = v
            else:
                k = None
            if isinstance(v, list):
                v = FieldMap(v)
            elif isinstance(v, str):
                # Allow using fields without direct import
                v = parse_field_spec(v)
            elif isinstance(v, (int, long)):
                v = Bytes(v)
            fields.append(v)
            if k is not None:
                names[k] = i
                properties[k] = property(getter(i), setter(i))
            name_l.append(k)
        self.names = names
        properties['_asdict'] = lambda self: dict((n, getattr(self, n)) for n in names)

        def map_repr(self):
            res = ["<%s instance:" % (type(self).__name__,)]
            for i, k in enumerate(name_l):
                v_rep = repr(self[i]).splitlines(False)
                if k is not None:
                    v_rep[0] = ("%s = " % k) + v_rep[0]
                else:
                    v_rep[0] = ("[%d]: " % i) + v_rep[0]
                for l in v_rep:
                    res.append("   " + l)
            res.append('>')
            return '\n'.join(res)
        properties['__repr__'] = map_repr
        super(FieldMap, self).__init__(fields)
        self._bound = type("BoundFieldMap", (self._bound, ), properties)


if __name__ == '__main__':
    test = bytearray.fromhex('1234567890abcdef'*3)
    f = FieldMap([("a", uint16), ("b", uint32), ("c", uint64), ("d", Bytes(10))])
    x = f.unpack(test)
    print x[::]
    print (x.a, x.b, x.c, x.d)

    f2 = FieldMap([("x", uint16), ("y", uint16), ("z", f)])
    test2 = bytearray("AABB") + test
    y = f2.unpack(test2)
    print y[::]
    print y.x, y.y, y.z, y.z.a, y.z.b, y.z.c

    f3 = FieldMap([
        ('foo', int16),
        ('bar', int16),
        ('bazz', [
            ("a", uint16),
            uint32,
            ("c", uint64),
            ("d", Bytes(10)),
        ])
    ])
    print f3.unpack(test2)

    f4 = FieldMap([
        ('foo', 'int16[2]'),
        [
            ("a", 'uint16'),
            'uint32',
            ("c", 'uint64'),
            ("d", 'Bytes(10)'),
        ]
    ])
    print f4.unpack(test2)

__all__ = ["uint8", "byte", "int8", "char",
           "uint16", "uint16l", "uint32",
           "uint32l", "uint64", "uint64l",
           "uint16b", "uint32b", "uint64b",
           "int16", "int16l", "int32", "int32l",
           "int64", "int64l", "int16b", "int32b",
           "int64b", "FieldSet", "FieldMap", "Bytes", "Array"]