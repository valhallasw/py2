import sys
import json
import reference

import subprocess
import sys

import logging
logging.basicConfig(level=logging.DEBUG)

import JSONListener
JSONListener.register()

#server = subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE, bufsize=0)

#(ip, port), authkey = json.loads(server.stdout.readline())
from six import b
(ip, port), authkey = (('127.0.0.1', 13337), b('a'))
#authkey = authkey.encode('latin-1')

from multiprocessing.managers import SyncManager as Manager

class FCManager(Manager):
    pass

FCManager.register('get_manager')

m = FCManager(address=(ip, port), authkey=authkey, serializer='json')
m.connect()

fcm = m.get_manager()

remote_import = reference.ProxyFactory(reference.Reference(fcm, fcm.get_global('__import__')[1]))
