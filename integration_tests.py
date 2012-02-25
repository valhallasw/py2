import unittest
import subprocess
import bPickleListener
bPickleListener.register()

from six import u, binary_type, text_type

import reference

def return_value(val):
    return val

def get_type(val):
    return text_type(type(val))

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ip, port), authkey = (('127.0.0.1', 13337),b'a')
        cls._server = subprocess.Popen(["python2", "server.py"])
        from multiprocessing.managers import SyncManager as Manager
        class FCManager(Manager):
                pass

        FCManager.register('get_manager')
        m = FCManager(address=(ip, port), authkey=authkey, serializer='bPickle')
        m.connect()
        fcm = m.get_manager()
        cls._remote_import = reference.ProxyFactory(reference.Reference(fcm, fcm.get_global('__import__')[1]))
        cls.tests = cls._remote_import('integration_tests')

    @classmethod
    def tearDownClass(cls):
        cls._server.kill()
        cls._server.wait()

    def test_str_stays_str(self):
        retval = self.tests.return_value(b'\xeb')
        assert(isinstance(retval, binary_type))
        assert(retval == b'\xeb')

    def test_unicode_stays_unicode(self):
        retval = self.tests.return_value(u('\u00eb'))
        assert(isinstance(retval, text_type))
        assert(retval == u('\u00eb'))

    def test_remote_type(self):
        retval = self.tests.get_type(b'\xeb')
        assert(retval == u("<type 'str'>"))
        retval = self.tests.get_type(u('\u00eb'))
        assert(retval == u("<type 'unicode'>"))
