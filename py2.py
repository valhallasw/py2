import subprocess
import json
from multiprocessing.managers import SyncManager as Manager

import bPickleListener
bPickleListener.register()

import reference

class FCManager(Manager):
    pass

FCManager.register('get_manager')

import os
serverpy = os.path.join(os.path.split(__file__)[0], 'server.py')

class Py2Obj(object):
    def __init__(self, cmd=["python2"], silent=True):
        self.cmd = cmd + [serverpy]
        if silent:
            self.cmd += ["-silent"]

        self._server = None
        self._manager = None
        self.__remote_import = None
        self._importcache = {}

    @property
    def manager(self):
        if not self._manager:
            self.make_connection()
        return self._manager

    @property
    def _remote_import(self):
        if not self.__remote_import:
            self.__remote_import = reference.ProxyFactory(reference.Reference(self.manager, self.manager.get_global('__import__')[1]))
        return self.__remote_import

    def make_connection(self):
        print("starting server")
        self._server = subprocess.Popen(self.cmd,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        bufsize=0)

        condata = self._server.stdout.readline()
        (ip, port), authkey = json.loads(condata.decode('latin-1'))
        authkey = authkey.encode('latin-1')

        m = FCManager(address=(ip, port), authkey=authkey, serializer='bPickle')
        m.connect()

        self._manager = m.get_manager()

    def rimport(self, module):
        if module not in self._importcache:
            self._importcache[module] = self._remote_import(module)
        return self._importcache[module]

py2 = Py2Obj()
