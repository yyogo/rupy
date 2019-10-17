from rupy import hexdump
import sys
nocolor = lambda x,*_: x
try:
    from termcolor import colored
except:
    colored = nocolor

COLORSCHEME = {
    'key': ('green', None, ['bold']),
    'index': ('blue',),
    'separator': ('yellow',),
    'tree': ('green',),
    'type': ('magenta', None, ['bold']),
    'value': ('white',),
    'hidden': ('blue',),
    'misc': ('magenta',),
}

class Colorizer:
    def __init__(self, color_func, scheme):
        def colorizer(c):
            def wrapped(x):
                return color_func(x, *c)
            return wrapped

        for name, attrs in scheme.items():
            setattr(self, name, colorizer(attrs))

AUTO = object()


DEFAULT_FILTER = lambda k, v: not ((isinstance(k, str) and k.startswith('_')) or v is None)

def pretty_print(value, key=None, maxdepth=-1, filter=DEFAULT_FILTER, limit=20, colors=AUTO, visited=None, last=True, indent='', **kwargs):
    """ pretty_print(value, [key=None, maxdepth=-1, hide_none=True, limit=20, colors=AUTO, indent='', **kwargs])

    Pretty-printing for nested structures, with colors.
    Arguments:
    * value - value to print.
    * key - optional key for "head" value.
    * maxdepth - stop at a certain nesting depth.
    * limit - only print this many items per container.
    * filter - Function accepting (key, value), items with False will be hidden
                (by default: None values and names starting with '_').
    * colors - True to always use, False to never use, AUTO (default) to automatically decide.
    * indent - indentation prefix for each line.
    * kwargs - additional keyword arguments passed to print().
    """

    if filter is None:
        filter = lambda k, v: True

    if colors is AUTO:
        # Check if stdout/file arg is a tty
        f = kwargs.get('file', sys.stdout)
        if hasattr(f, 'isatty') and f.isatty():
            colors = True
        else:
            colors = False
    c = Colorizer(colored if colors else nocolor, COLORSCHEME)

    if visited is None:
        visited = set()

    container = hasattr(value, '__iter__') and not isinstance(value, (bytes, str, bytearray))
    if container:
        start = '╞╘'[last]
        if hasattr(value, 'items'):
            items = ((str(k), v) for k, v in value.items())
        else:
            items = enumerate(value)

        if hasattr(container, '__len__'):
            length = len(container)
        else:
            items = list(items)
            length = len(items)
        if maxdepth is not None and maxdepth == 0:
            limit = 0
        items = ((k, v) for k, v in items if filter(k, v))
    else:
        start = '┝└'[last]
    if isinstance(key, int):
        key = c.index(f"[{key}]")
    elif key is not None:
        key = c.key(str(key))
    print(
        c.tree(f"{indent}{start} ") + (key or '') +
        c.separator(f"{' = ' if key  is not None else ''}"), end='', **kwargs)

    exindent = ('│ ', '  ')[last]

    if container:

        print(c.type(f"{value.__class__.__name__}  ") + c.misc(f'[len={length}]'), **kwargs)

        if id(value) in visited:
            print(c.tree(indent)
                + c.misc('  (recursion detected)'), **kwargs)
            return

        i = 0
        for i, (k, v) in enumerate(items):
            if limit is not None and i + 1 >= limit:
                break
            pretty_print(
                value=v,
                key=k,
                maxdepth=maxdepth - 1 if maxdepth is not None else None,
                indent=indent + exindent,
                last=i + 1 == length,
                filter=filter,
                visited=visited | {id(value)},
                limit=limit,
                colors=colors,
                **kwargs)
        if i < length - 1:
            print(c.tree(indent + exindent )
                + c.hidden(f'⋮   ({length - i} items hidden)'), **kwargs)

    else:
        val = repr(value)
        if isinstance(value, (bytes, bytearray)):
            if any(x < 32 or x > 127 for x in value):
                if len(value) > 100:
                    hd = hexdump(value, prefix=indent + exindent)
                    hd.snipfmt = c.tree('{self.prefix}') + c.hidden('⋮         [0x{bytes:x} hidden bytes]')
                    hd.dupfmt = c.tree('{self.prefix}') + c.hidden('⋮         [0x{lines:x} duplicate lines]')
                    hd.fmt = (c.tree('{self.prefix}│ ')
                            + c.index('{offset:{self.offsetfmt}}') + '  '
                            + c.value('{dump}') +  '  '
                            + c.misc('{asc:{self.width}}') +  '  ' )
                    print(c.misc('(hexdump)'), **kwargs)
                    print(hd.partial(skip_dups=1), **kwargs)
                    return
                else:
                    val = c.misc('(hex) ') + c.value(value.hex())
        if isinstance(value, str) and hasattr(value, '__int__'):
            # special case for construct enums and similar types
            val = f'{value}' + c.misc(f' ({int(value):#x})')

        elif hasattr(value, '__len__'):
            val += c.misc(f' [len={len(value)}]')
        if len(val) > 150:
            val = c.value(val[:100]) + c.hidden("...") + c.value(val[-50:])
        else:
            val = c.value(val)
        # special
        print(val, **kwargs)


pp = pretty_print
__all__ = ["pp", "pretty_print"]
