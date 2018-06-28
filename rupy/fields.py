from __future__ import print_function
import struct
import re

import operator

from rupy.buf import buf
from rupy.compat import *

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


u8 = byte = BasicField("<B")
i8 = char = BasicField('<b')
u16 = u16l = BasicField("<H")
u32 = u32l = BasicField("<L")
u64 = u64l = BasicField("<Q")
u16b = BasicField(">H")
u32b = BasicField(">L")
u64b = BasicField(">Q")
i16 = i16l = BasicField("<h")
i32 = i32l = BasicField("<l")
i64 = i64l = BasicField("<q")
i16b = BasicField(">h")
i32b = BasicField(">l")
i64b = BasicField(">q")

@compatible
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
            return tuple(self[i] for i in range(*item.indices(len(self))))
        return self._fieldset.get(self.__buffer__, item)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            r = range(key.indices(len(self)))
            if len(value) != len(r):
                raise ValueError("mismatched value count in field assignment")
            for i, x in zip(r, value):
                self._fieldset.set(self.__buffer__, i, x)
        else:
            self._fieldset.set(self.__buffer__, key, value)

    def __bytes__(self):
        buf = bytearray(self._fieldset.size)
        self._fieldset.pack(buf, self)
        return bytes(buf)

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

__all__ = ["u8", "byte", "i8", "char",
           "u16", "u16l", "u32",
           "u32l", "u64", "u64l",
           "u16b", "u32b", "u64b",
           "i16", "i16l", "i32", "i32l",
           "i64", "i64l", "i16b", "i32b",
           "i64b", "FieldSet", "FieldMap", "Bytes", "Array"]

def parse_dsl(s):
    """
    I'm a horrible person
    """
    # tokenize
    tokens, leftover = re.Scanner(
        [
            (r'[a-zA-Z_]\w*', lambda s, m: ('name', m)),
            (r'\d+', lambda s, m: ('literal', int(m))),
            (r'[\(\[\{]', lambda s,m :('bracket_open', m)),
            (r'[\)\]\}]', lambda s,m :('bracket_close', m)),
            (r'\:', ('op_colon', None)),
            (r'\s+', None),
        ]
    ).scan(s)
    if leftover:
        raise ValueError("Syntax error in fieldspec: invalid token at %d" % (len(s) - len(leftover)))

    matching_bracket = {'(': ')', '[': ']', '{': '}', None: None}
    def bracketeer(it, btype=None):
        """ Group by brackets (recursively) """
        level = []
        for token, value in it:
            if token == 'bracket_open':
                level.append(bracketeer(it, value))
            elif token == 'bracket_close':
                if value != matching_bracket[btype]:
                    raise ValueError("Syntax error in fieldspec: mismatched brackets")
                return ('brackets%s' % btype, level)
            else:
                level.append((token, value))
        if btype is not None:
            raise ValueError("Syntax error in fieldspec: unmatched brackets")
        return level

    tokens = bracketeer(iter(tokens))
    # top level is by default a {}
    if len(tokens) == 1 and tokens[0][0] == 'brackets{':
        tokens = tokens[0][1]

    def colonize(tokens):
        # handle colons and named fields etc.
        last = None
        res = []
        it = iter(tokens)

        # iterate over tokens, save each one
        # if it is followed by a colon - get the next token and pair them
        # if not, save it as a nameless field
        for (token, value) in it:
            if token == 'op_colon':
                try:
                    ftype = next(it)
                except StopIteration:
                    raise ValueError("Error in fieldspec: no field type specified")
                if last is None:
                    raise ValueError("Error in fieldspec: no field name specified")
                if last[0] != 'name':
                    raise ValueError("Invalid field name")
                fname = last[1]
                last = None
            else:
                # last one may have been a nameless field
                fname = None
                ftype = last
                last = token, value
            res.append((fname, ftype))
        if last is not None:
            # last member is nameless
            res.append((None, last))

        res2 = []
        # Parse field types
        for fname, ftype in res:
            if ftype is None:
                continue
            if ftype[0] == 'name':
                # Type is a name, get it from the list
                field = TYPES[ftype[1]]
            elif ftype[0] == 'fieldtype':
                # Type is complex, use it
                field = ftype[1]
            elif ftype[0] == 'literal':
                # Literal number as shorthand for byte field
                field = Bytes(ftype[1])
            else:
                raise ValueError("Error in fieldspec: invalid field type ({!r})".format(ftype))
            res2.append((fname, field))
        return res2

    def groupy(tokens):
        # Handle arrays and complex types
        last = None
        res = []
        for t, v in tokens:
            if t == 'brackets[' or t == 'brackets(':
                # Field is an array
                if len(v) != 1 or v[0][0] != 'literal':
                    raise ValueError("Error in fieldspec: invalid array")
                if len(res) == 0:
                    raise ValueError("Error in fieldspec: no field to make array of")
                last = res.pop(-1)
                if last[0] == 'name':
                    field = TYPES[last[1]]
                elif last[0] == 'fieldtype':
                    field = last[1]
                else:
                    raise ValueError("Invalid array type")

                if field == Bytes:
                    arr = Bytes(v[0][1])
                else:
                    arr = Array(field,  v[0][1])
                res.append(('fieldtype', arr))
            elif t == 'brackets{':
                result = groupy(v)
                res.append(('fieldtype', result))
            else:
                res.append((t, v))
        return colonize(res)


    return groupy(tokens)


class FieldMap(FieldSet):
    """
    DOCME
    """
    def __init__(self, fieldspec):
        fields = []
        names = {}
        name_l = []
        properties = {}

        if isinstance(fieldspec, str):
            fieldspec = parse_dsl(fieldspec)

        for i, v in enumerate(fieldspec):
            if isinstance(v, tuple):
                k, v = v
            else:
                k = None
            if isinstance(v, list):
                v = FieldMap(v)
            elif isinstance(v, str):
                v = parse_dsl(v)
                if len(v) != 1:
                    raise ValueError("Invalid field value")
                k2, v= v[0]
                if k2 is not None:
                    if k is not None:
                        raise ValueError("Field named twice")
                    k = k2

            elif isinstance(v, int):
                v = Bytes(v)
            fields.append(v)
            if k is not None:
                if k in names:
                    raise ValueError("Field named %r already defined" % k)
                names[k] = i
                properties[k] = property(getter(i), setter(i))
            name_l.append(k)
        self.names = names
        properties['_asdict'] = lambda self: dict((n, getattr(self, n)) for n in names)

        def map_repr(self):
            res = ["<%d fields:" % (len(self), )]
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

TYPES = {x: globals()[x] for x in __all__}

if __name__ == '__main__':
    test = bytearray.fromhex('1234567890abcdef'*3)
    f = FieldMap([("a", u16), ("b", u32), ("c", u64), ("d", Bytes(10))])
    x = f.unpack(test)
    print(x[::])
    print((x.a, x.b, x.c, x.d))

    f2 = FieldMap([("x", u16), ("y", u16), ("z", f)])
    test2 = bytearray(b"AABB") + test
    y = f2.unpack(test2)
    print(y[::])
    print((y.x, y.y, y.z, y.z.a, y.z.b, y.z.c))

    f3 = FieldMap([
        ('foo', i16),
        ('bar', i16),
        ('bazz', [
            ("a", u16),
            u32,
            ("c", u64),
            ("d", Bytes(10)),
        ])
    ])
    print(f3.unpack(test2))

    f4 = FieldMap([
        ('foo', 'i16[2]'),
        [
            ("a", 'u16'),
            'u32',
            ("c", 'u64'),
            ("d", 'Bytes(10)'),
        ]
    ])


    print(f4.unpack(test2))

    f5 = FieldMap("""
        foo: i16[2]
        {
            a: u16
            u32
            c: u64
            d: Bytes(10)
        }
    """)

    print(f5.unpack(test2))



