__author__ = "rumbah"
from rupy.compat import *

@compatible
class HexDump(object):
    """
    HexDump(data, width=16, groups=(2,4), prefix='')

    Dump hex.

    width - Number of bytes per dump line
    groups - How to group the bytes, i.e where to put spaces. Ex:
             (1,) - space after every byte
             (2,4) - space after every two bytes, and another after
                     every 4 2-byte groups
    prefix - Optional prefix for each line in the dump
    """
    fmt = u'{self.prefix}{offset:06x}| {dump} |{asc:{self.width}}|'
    snipfmt = u'{self.prefix}...    [0x{bytes:x} hidden bytes]'
    dupfmt = u'{self.prefix}***    [0x{lines:x} duplicate lines]'
    ascii_trans = bytearray(x if 32 <= x < 127 else b'.'[0] for x in range(256))

    def __init__(self, data, width=16, groups=(2, 4), prefix=''):
        self.data = data
        self._mv = memoryview(data)  # to support all buffer types
        self.width = width
        self.groups = groups
        self.length = len(data)
        self.prefix = prefix
        pattern = [u'{}'] * self.width
        for g in groups:
            pattern = [''.join(pattern[i:i + g]) +
                       ' ' for i in range(0, width, g)]
        self._dump_fmt_pattern = ''.join(pattern).strip()
        self._dump_fmt = self._dump_fmt_pattern.format(
            *([u'{:02x}'] * self.width))

    def __len__(self):
        """ len(hd) <=> hd.__len__
        Return the number of lines in the hexdump
        """
        return (self.length + self.width - 1) // self.width

    def _format_line(self, offset, data):
        data = bytearray(data)
        if len(data) < self.width:  # partial line
            dump_fmt = self._dump_fmt_pattern.format(
                *([u'{:02x}'] * len(data) + [u'  '] * (self.width - len(data))))
        else:
            dump_fmt = self._dump_fmt
        asc = data.translate(self.ascii_trans).decode('ascii')
        return self.fmt.format(
            offset=offset, dump=dump_fmt.format(*data), asc=asc, self=self)

    def __getitem__(self, index):
        if isinstance(index, (int, long)):
            if index < 0:
                index += len(self)
            offset = index * self.width
            if offset < 0 or offset >= len(self._mv):
                raise IndexError(offset)
            return self._format_line(offset, self._mv[offset:offset+self.width])
        else:
            return [self[i] for i in range(*index.indices(len(self)))]

    def dump(self, snip=None, skip_dups=False):
        """ Get a formatted dump.
        snip: Maximum number of lines to show in the output
        skip_dups: Set true to skip duplicate lines
        """
        if snip is None:
            head = len(self)
        else:
            head = max(0, snip - 4) # show at most 3 lines from the end

        if not skip_dups and head + 4 >= len(self):
            # Nothing to hide
            return u'\n'.join(self)

        last = None
        skipped = False
        lines = []
        i = 0
        for i in range(len(self)):
            l = self._mv[i * self.width:(i + 1) * self.width]
            if l == last and skip_dups:
                if skipped == 0:
                    lines.append(None)  # some guard thing
                skipped += 1
                continue
            else:
                if skipped > 0:
                    lines[-1] = (self.dupfmt.format(self=self, lines=skipped))
                    skipped = 0
                lines.append(self._format_line(i * self.width, l))

            if len(lines) >= head and len(self) - i > 4:  # Only break if we need to snip
                break
            last = l

        if skipped > 0:  # In case we skip all the way to the end... Ugly but essential
            lines[-1] = (self.dupfmt.format(self=self, lines=skipped))

        snipped = len(self) - i - 4
        if snipped > 0:
            lines.append(self.snipfmt.format(self=self, bytes=snipped * self.width))
            lines += self[-3:]

        return u'\n'.join(lines)

    def partial(self, snip=20, skip_dups=False):
        return self.dump(snip, skip_dups)

    def __bytes__(self):
        return self.dump().encode('ascii')

    def __unicode__(self):
        return self.dump()

    def __repr__(self):
        return "<%r of %r object, %s bytes:\n%s >" % (self.__class__.__name__,
            type(self.data).__name__, self.length, HexDump(
                self.data, width=self.width, groups=self.groups, prefix='  '
            ).dump(15, True).rstrip()
        )

hd = hexdump = HexDump
