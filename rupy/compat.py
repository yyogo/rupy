import sys

def metabase(metaclass, *bases):
    if len(bases) == 0:
        bases = object,
    base = metaclass('%s meta-base' % metaclass, bases, {})
    return base

if sys.version_info.major == 2:
    # Python 2.x compatibility
    from future_builtins import *
    range = xrange  # Every time I see 'range' used in a for loop I cringe
    def compatible(object):
        if hasattr(object, "__bytes__"):
            object.__str__ = object.__bytes__
        if hasattr(object, "__next__"):
            object.next = object.__next__

        return object

else:
    # Python 3.x compatibility
    long = int
    buffer = memoryview  # in 2.x these are not compatible in some builtins for some stupid reason
    file = type("file", (), {})
    def compatible(object):
        if hasattr(object, "__unicode__"):
            setattr(object, "__str__", object.__unicode__)
        return object

del sys
