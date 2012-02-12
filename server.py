from multiprocessing.managers import SyncManager as Manager

import JSONListener
JSONListener.register()

import sys
import reference
import json
from six import print_

import logging
logging.basicConfig(level=logging.DEBUG)

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

m = FCManager(address=('127.0.0.1', 13337), serializer='json', authkey='a')
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