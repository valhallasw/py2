import reference
import unittest

class FauxConnectionTests(unittest.TestCase):
    def setUp(self):
        self.fxconn_object = self._new_fxconn_object()
    
    def _new_fxconn_object(self):
        return reference.FauxConnection()

    def test_fxconn_testReferenceIsPerObject(self):
        C = self.fxconn_object
        D = self._new_fxconn_object()
        assert(id(C.references) != id(D.references))

    def test_fxconn_testGetGlobal(self):
        C = self.fxconn_object
        isreference, value = C.get_global('__name__')
        assert(not isreference)
        assert(value == reference.__name__)

    def test_fxconn_testGetGlobalRef(self):
        C = self.fxconn_object
        isreference, value = C.get_global('int')
        assert(isreference)

    def test_fxconn_getAttributeOfGlobal(self):
        C = self.fxconn_object
        
        isreference, int_ref = C.get_global('int')
        isreference, value = C.get_attribute(int_ref, '__doc__')
        assert(not isreference)
        assert(value == int.__doc__)
        
    def test_fxconn_callObject(self):
        C = self.fxconn_object
        isreference, int_ref = C.get_global('int')
        isreference, value = C.call(int_ref, (False, 1))

        assert(not isreference)
        assert(value == 1)

    def test_fxconn_callFunctionOnRemoteObject(self):
        C = self.fxconn_object
        isreference, list_ref = C.get_global('list')
        assert(isreference)
        isreference, remote_list_ref = C.call(list_ref, (False, (1,2,3)))
        assert(isreference)
        isreference, len_ref = C.get_global('len')
        assert(isreference)
        isreference, value = C.call(len_ref, (True, remote_list_ref))
        assert(not isreference)
        assert(value == 3)

    def test_fxconn_dir_str_repr(self):
        C = self.fxconn_object
        isreference, list_ref = C.get_global('list')
        assert(isreference)
        assert(C.dir(list_ref) == dir(list))
        assert(C.str(list_ref) == str(list))
        assert(C.repr(list_ref) == repr(list))

    def test_unicode_stays_unicode(self):
        C = self.fxconn_object
        isreference, ref = C.get_global('unicode')
        assert(isreference)
        isreference, unicode_object = C.call(ref, (False, "\u00eb"))
        assert(not isreference)
        assert(isinstance(unicode_object, unicode))

    def test_str_stays_str(self):
        C = self.fxconn_object
        isreference, ref = C.get_global('str')
        assert(isreference)
        isreference, str_object = C.call(ref, (False, "\x89"))
        assert(not isreference)
        assert(isinstance(str_object, str))


class ReferenceTest(unittest.TestCase):
    def setUp(self):
        self.connection = reference.FauxConnection()
        isreference, ref = self.connection.get_global('int')
        assert(isreference)
        self.reference = reference.Reference(self.connection, ref)

    def test_call(self):
        isreference, value = self.reference.call(1)
        assert(not isreference)
        assert(value == 1)

    def test_get_attribute(self):
        isreference, value = self.reference.get_attribute('__doc__')
        assert(not isreference)
        assert(value == int.__doc__)

    def test_dir_str_repr(self):
        assert(self.reference.dir() == dir(int))
        assert(self.reference.str() == str(int))
        assert(self.reference.repr() == repr(int))

class ProxyFactoryTest(unittest.TestCase):
    def testType(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('int')
        r = reference.Reference(connection, ref)
        proxyobject = reference.ProxyFactory(r)
        assert(isinstance(proxyobject, reference.ProxyBase))

    def testGetNonRefAttribute(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('int')
        r = reference.Reference(connection, ref)
        proxyobject = reference.ProxyFactory(r)
        assert(proxyobject.__name__ == 'int')

    def testCreateObject(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('int')
        r = reference.Reference(connection, ref)
        proxyobject = reference.ProxyFactory(r)
        assert(proxyobject(1) == 1) 
        assert(isinstance(proxyobject(1), proxyobject))

    def testComplicatedObject(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('__import__')
        r = reference.Reference(connection, ref)
        remote_import = reference.ProxyFactory(r)
        assert(isinstance(remote_import, reference.ProxyBase))
        remote_datetime = remote_import('datetime')
        assert(isinstance(remote_datetime, reference.ProxyBase))
        remote_datetime_class = remote_datetime.datetime
        assert(isinstance(remote_datetime_class, reference.ProxyBase))
        remote_gvr_bday = remote_datetime_class(1956, 1, 31)
        assert(isinstance(remote_gvr_bday, reference.ProxyBase))
        local_gvr_bday_string = remote_gvr_bday.isoformat()
        assert(isinstance(local_gvr_bday_string, basestring))
        assert(local_gvr_bday_string == '1956-01-31T00:00:00')

    def testCallFnOnObject(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('builtins')
        r = reference.Reference(connection, ref)
        remote_builtins = reference.ProxyFactory(r)
        remote_list = remote_builtins.list((1,2,3))
        remote_len  = remote_builtins.len
        assert(remote_len(remote_list) == 3)
    
    def testSpecialFunctionsWrapper(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('list')
        r = reference.Reference(connection, ref)
        proxyobject = reference.ProxyFactory(r)
        assert(proxyobject((1,2,3)).__getitem__(1) == 2)

    def testdir_str_repr(self):
        connection = reference.FauxConnection()
        isreference, ref = connection.get_global('list')
        r = reference.Reference(connection, ref)
        proxyobject = reference.ProxyFactory(r)
        assert(dir(proxyobject) == dir(list))
        assert(repr(list) in repr(proxyobject))
        assert(str(list) in str(proxyobject))
