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

class JSONListener(Listener):
    def accept(self):
        obj = Listener.accept(self)
        return ConnectionWrapper(obj, json.dumps, json.loads)

def JSONClient(*args, **kwds):
    return ConnectionWrapper(Client(*args, **kwds), json.dumps, json.loads)

def register(key='json'):
    from multiprocessing.managers import listener_client
    listener_client[key] = (JSONListener, JSONClient)
