# Based on multiprocessing/connection.py (c) 2006-2008, R Oudkerk

from multiprocessing.connection import Listener, Client, ConnectionWrapper
from six import text_type, binary_type
from six import u,b
from six import print_

import os
pid = os.getpid()

from bytestrpickle import BytestrPickler, BytestrUnpickler 
import io

def dumps(data):
    f = io.BytesIO()
    data = list(data)
    if isinstance(data[0], text_type):
        data[0] = b.encode('ascii')
    BytestrPickler(f, protocol=2).dump(data)
    return f.getvalue()

def loads(data):
    data = BytestrUnpickler(io.BytesIO(data)).load()
    data = list(data)
    if isinstance(data[0], binary_type):
        data[0] = data[0].decode('ascii')  # python 2 will coerce it back...
    return data

class bPickleListener(Listener):
    def accept(self):
        obj = Listener.accept(self)
        return ConnectionWrapper(obj, dumps, loads)

def bPickleClient(*args, **kwds):
    return ConnectionWrapper(Client(*args, **kwds), dumps, loads)

def register(key='bPickle'):
    import multiprocessing.managers
    from multiprocessing.managers import listener_client
    listener_client[key] = (bPickleListener, bPickleClient)

    oldMPT = multiprocessing.managers.MakeProxyType
    def newMPT(name, exposed):
        exposed = [x.decode('ascii') for x in exposed]
        return oldMPT(name, exposed)
    multiprocessing.managers.MakeProxyType = newMPT

