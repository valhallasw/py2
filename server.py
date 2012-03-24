from multiprocessing.managers import SyncManager as Manager

import bPickleListener
bPickleListener.register()

import sys
import reference
import json
from six import print_

import logging
if "-silent" not in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)

fc = reference.FauxConnection()

class FCManager(Manager):
    pass

FCManager.register('get_manager', lambda: fc)

m = FCManager(address=('127.0.0.1', 13338), serializer='bPickle', authkey='a')
m.start()

print_(json.dumps([m._address, m._authkey.decode('latin-1')]))
sys.stdout.flush()

x = True
while x:
    try:
        x = sys.stdin.read()
    except KeyboardInterrupt:
        print "(python2 server) ignoring KeyboardInterrupt. Use ^D to quit when running directly."
