#
# A higher level module for using sockets (or Windows named pipes)
#
# multiprocessing/connection.py
#
# Copyright (c) 2006-2008, R Oudkerk --- see COPYING.txt
#

from multiprocessing.connection import Listener, Client, ConnectionWrapper

try:
    import simplejson as json
except ImportError:
    import json

def dumps(data):
    return json.dumps(data).encode('latin-1')

def loads(data):
    return json.loads(data.decode('latin-1'))

class JSONListener(Listener):
    def accept(self):
        obj = Listener.accept(self)
        return ConnectionWrapper(obj, dumps, loads)

def JSONClient(*args, **kwds):
    return ConnectionWrapper(Client(*args, **kwds), dumps, loads)

def register(key='json'):
    from multiprocessing.managers import listener_client
    listener_client[key] = (JSONListener, JSONClient)
