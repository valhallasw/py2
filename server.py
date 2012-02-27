from multiprocessing.managers import SyncManager as Manager

import bPickleListener
bPickleListener.register()

import sys
import reference
import json
from six import print_

import logging
if "-silent" not in sys.argv:
    print sys.argv
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

fc = reference.FauxConnection()

class FCManager(Manager):
    pass

#for fun in ['get_global', 'call', 'get_attribute', 'destroy']:
#    def wrapfungen(fun):
#        def wrapfun(*args, **kwargs):
#            res = getattr(fc, fun)(*args, **kwargs)
#            print fun, args, kwargs, "->", res
#            return res
#        return wrapfun
#    
#    FCManager.register(fun,wrapfungen(fun))

FCManager.register('get_manager', lambda: fc)

m = FCManager(address=('127.0.0.1', 13337), serializer='bPickle', authkey='a')
s = m.get_server()

print_(json.dumps([s.address, s.authkey.decode('latin-1')]))
sys.stdout.flush()
print dir(s)
import threading

#class JetzerThread(threading.Thread):
#def run(self):
#        s.serve_forever()
#
#JetzerThread().start()

import os; print os.getpid()

s.serve_forever()
