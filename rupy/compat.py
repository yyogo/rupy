import sys

def metabase(metaclass, *bases):
    if len(bases) == 0:
        bases = object,
    base = metaclass('%s meta-base' % metaclass, bases, {})
    return base

if sys.version_info.major == 2:
    PY_VERSION = 2
    # Python 2.x compatibility
    from future_builtins import *
    range = xrange  # No real need for range() over xrange()
    def compatible(cls):
        if hasattr(cls, "__bytes__"):
            cls.__str__ = cls.__bytes__
        if hasattr(cls, "__next__"):
            cls.next = cls.__next__

        return cls

else:
    PY_VERSION = 3
    # Python 3.x compatibility
    long = int
    buffer = memoryview  # in 2.x these are not compatible in some builtins for some stupid reason
    file = type("file", (), {})
    unicode = str
    def compatible(cls):
        if hasattr(cls, "__unicode__"):
            setattr(cls, "__str__", cls.__unicode__)
        return cls

del sys
