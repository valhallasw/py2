""" An adaptation of pickle that directly links py2 str to py3 bytes, both when
    writing and when reading. This means it is possible to write protocol=2
    pickles containing byte objects (that will be written as python2 str),
    as well as reading py2 str with non-ascii characters (and instead of being
    converted to py3 string, they will be read as py3 bytes.

    (C) 2012, Merlijn van Deen <valhallasw@gmail.com>.
    Licensed under the MIT license.

    BytestrPickler.save_bytes was based on _Pickler.save_bytes in
    Python 2, (C) 2001-2012 Python Software Foundation
"""

import pickle
import pickletools
import struct

class BytestrUnpickler(pickle._Unpickler):
    """
    An adaptation of pickle._Unpickler that loads python 2 "str" as python 3
    "bytes".
    """

    def __init__(self, file, fix_imports=True):
        super().__init__(file, fix_imports=fix_imports, \
                         encoding="latin-1",
                         errors="strict")
        self.dispatch = self.dispatch.copy()
        opcodes_to_wrap = [x.code.encode('ascii')[0] for x in pickletools.opcodes if x.stack_after == [pickletools.pystring]]
        for opcode in opcodes_to_wrap:
            self.dispatch[opcode] = self._byteify(self.dispatch[opcode])

    def _byteify(self, dispatcher):
        def load_bytetype(obj):
            dispatcher(obj)
            obj.stack[-1] = obj.stack[-1].encode('latin-1')
        return load_bytetype

class BytestrPickler(pickle._Pickler):
    """ An adaptation of pickle._Pickler that writes 'bytes' as py2 'str's """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dispatch = self.dispatch.copy()
        self.dispatch[bytes] = self.save_bytes

    def save_bytes(s, self, obj, pack=struct.pack):
        if self.proto >= 3:
            super().save_bytes(obj, pack)
            return

        # The following has been directly based on the pickle code in python 2
        if self.bin:
            n = len(obj)
            if n < 256:
                self.write(pickle.SHORT_BINSTRING + chr(n).encode('latin-1') + obj)
            else:
                self.write(pickle.BINSTRING + pack("<i", n) + obj)
        else:
            self.write(pickle.STRING + repr(obj).lstrip('b').encode('ascii') + b'\n')
        self.memoize(obj)
