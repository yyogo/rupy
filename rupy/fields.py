from __future__ import print_function
import struct
import re
import sys

import operator

from rupy.buf import buf
from rupy.bitview import BitView
from rupy.compat import *

class BasicField(object):
    def __init__(self, fmt):
        self.st = struct.Struct(fmt)
        self.size = self.st.size

    def unpack(self, buf):
        return self.st.unpack(buf)[0]

    def pack(self, buf, data):
        self.st.pack_into(buf, 0, data)

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
f32 = BasicField("<f")
f64 = BasicField("<d")

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

@compatible
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

@compatible
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
        if isinstance(fieldspec, dict):
            fieldspec = list(fieldspec.items())

        #print(fieldspec)
        for i, v in enumerate(fieldspec):
            if isinstance(v, tuple):
                k, v = v
            else:
                k = None
            if isinstance(v, (list, tuple, dict)):
                v = FieldMap(v)
            fields.append(v)
            if k is not None:
                if k in names:
                    raise ValueError("Field named %r already defined" % k)
                names[k] = i
                properties[k] = property(getter(i), setter(i))
            name_l.append(k)
        self.names = names

        super(FieldMap, self).__init__(fields)

        if any(self.names):
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

            properties['_asdict'] = lambda self: dict((n, getattr(self, n)) for n in names)
            properties['__repr__'] = map_repr
            self._bound = type("BoundFieldMap", (self._bound, ), properties)


@compatible
class BytesView(object):
    def __init__(self, mem):
        self._mem = mem

    def __getitem__(self, sl):
        return self._mem[sl]

    def __setitem__(self, sl, val):
        self._mem[sl] = val

    def __repr__(self):
        return f'<{self._mem.hex()}>'

    def __bytes__(self):
        return bytes(self._mem)

    def __len__(self):
        return len(self._mem)

    def hex(self):
        return bytes(self).hex()

    @property
    def bits(self):
        return BitView(self._mem)

    def __iter__(self):
        return iter(self._mem)

    def __eq__(self, other):
        return self._mem == other

    def fields(self, spec):
        fm = FieldMap(spec)
        return fm.unpack(self._mem)

class Bytes(object):
    buftype = BytesView
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

    def __eq__(self, other):
        if isinstance(other, Bytes):
            return self.size == other.size
        return NotImplemented


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
           "i64b", "f32", "f64", 
           "FieldSet", "FieldMap", "Bytes"]

def parse_dsl(s):
    """ Parse the fields() DSL. Grammer:

        fields: (field [ ',' ])*
        field: [identifier ':' ] type

        type: typename
            | array
            | struct
        typename: identifier
        array: type '[' integer ']'
        struct: '{' fields '}
        
        integer: '0x' hex_numeral 
               | '0o' octal_numeral
               | '0b' binary_numeral
               | decimal

        hex_numeral: ('0'...'9' | 'a'...'f')+
        octal_numeral: '0'...'8'+
        binary_numeral: ('0' | '1')+
        decimal: ('1'...'9') digit*
        digit: '0'...'9'

        identifier: alpha alphanumeric*
        alpha: ('a'...'z' | 'A'...'Z' | '_')
        alphanumeric: alpha | digit

    Tests:
    
    >>> parse_dsl("u8") == [(None, u8)]
    True
    >>> parse_dsl("f64[4]") == [(None, [f64] * 4)]
    True
    >>> parse_dsl("foo: bytes[32]") == [('foo', Bytes(32))]
    True
    >>> parse_dsl("foo: u8, bar: u8, bazz: { foo: u32 }[4]") == [('foo', u8), ('bar', u8), ('bazz', [[('foo', u32)]] * 4)]
    True
    >>> parse_dsl("u32[32], u32[0x20], u32[0o40], u32[0b100000]") == [(None, [u32] * 32)] * 4
    True
    """
    # tokenize
    tokens, leftover = re.Scanner(
        [
            (r'[a-zA-Z_]\w*', lambda s, m: ('identifier', m)),
            (r'(0[xob])?\d+', lambda s, m: ('literal', int(m, 0))),
            (r'[\(\[\{]', lambda s,m :('bracket_open', m)),
            (r'[\)\]\}]', lambda s,m :('bracket_close', m)),
            (r'\:', ('op_colon', None)),
            (r',', ('op_comma', None)),
            (r'\s+', None),
        ]
    ).scan(s)
    if leftover:
        raise ValueError("Syntax error in fieldspec: invalid token at %d" % (len(s) - len(leftover)))

    def parse_struct(tokens):
        fields = []
        while tokens and tokens[0] != ('bracket_close', '}'):
            field = parse_field(tokens)
            fields.append(field)
            if tokens and tokens[0][0] == 'op_comma':
                tokens.pop(0)
        if not tokens:
            raise ValueError("Unclosed struct")
        tokens.pop(0)
        return fields
    
    def make_array(ft, count):
        if ft is Bytes or ft is byte:
            return Bytes(count)
        else:
            return [ft] * count

    def parse_field_type(tokens):
        tok, val = tokens.pop(0)
        if tok == 'identifier':
            ftype = TYPES[val]
        elif tok == 'bracket_open' and val == '{':
            ftype = parse_struct(tokens)
        else:
            raise ValueError("invalid field type")
        # parse array 
        while tokens and tokens[0][0] == 'bracket_open' and tokens[0][1] in '([':
            _, brack = tokens.pop(0)
            tok, val = tokens.pop(0)
            if tok != 'literal':
                raise ValueError("Invalid array length specifier")
            closing = {'(': ')', '[': ']'}[brack]
            if tokens.pop(0) != ('bracket_close', closing):
                raise ValueError("unmatched array bracket")
            ftype = make_array(ftype, val)
        return ftype

    def parse_field(tokens):
        tok, val = tokens[0]
        if tok == 'identifier' and len(tokens) > 1 and tokens[1][0] == "op_colon":
            del tokens[:2]
            name = val
        else:
            name = None
        ftype = parse_field_type(tokens)
        return (name, ftype)
    
    fields = []
    while tokens:
        fields.append(parse_field(tokens))
        if tokens and tokens[0][0] == 'op_comma':
            tokens.pop(0)
    return fields


TYPES = {x: globals()[x] for x in __all__}
TYPES.update({'bytes': Bytes})

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

    f4 = FieldMap({
        'foo': [i16, i16],
        'bar': {
            "a": u16,
            "b": u32,
            "c": u64,
            "d": Bytes(10)
        }
    })


    print(f4.unpack(test2))

    f5 = FieldMap("""
        foo: i16[2]
        {
            a: u16
            u32
            c: u64
            d: Bytes[10]
        }
    """)

    print(f5.unpack(test2))



