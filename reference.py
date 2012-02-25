from six.moves import builtins
from six import text_type, binary_type, iteritems
import logging

__logger__ = logging.getLogger(__file__)

import functools
from numbers import Number
import json

# we only transfer these objects over the connection
transferTypes = (Number, text_type, binary_type)

class ProxyBase(object):
    def __init__(self):
        reference = object.__getattribute__(self, '_reference')
        __logger__.debug('%s: initialized for %r', object.__repr__(self), reference)

    def __getattribute__(self, attribute):
        reference = object.__getattribute__(self, '_reference')
        __logger__.debug('%s: retrieving %r from %r', object.__repr__(self), attribute, reference)
        isreference, retval = reference.get_attribute(attribute)
        if isreference:
            return ProxyFactory(retval)
        else:
            return retval

    def __call__(self, *args, **kwargs):
        reference = object.__getattribute__(self, '_reference')
        __logger__.debug('%s: calling', object.__repr__(reference))
        def unwrap_item(item):
            if isinstance(item, ProxyBase):
                return object.__getattribute__(item, '_reference')
            elif isinstance(item, tuple):
                return tuple(unwrap_item(obj) for obj in item)
            else:
                return item

        def unwrap(args, kwargs):
            args = [unwrap_item(item) for item in args]
            kwargs = dict((key, unwrap_item(value)) for (key, value) in kwargs)
            return args, kwargs

        args, kwargs = unwrap(args, kwargs)
        isreference, retval = reference.call(*args, **kwargs)

        def wrap_item(isreference, item):
            if isreference:
                return ProxyFactory(retval)
            elif isinstance(item, tuple):
                return tuple(wrap_item(*obj) for obj in item)
            else:
                return item
        
        return wrap_item(isreference, retval)

    def __dir__(self):
        reference = object.__getattribute__(self, '_reference')
        return reference.dir()

    def __repr__(self):
        reference = object.__getattribute__(self, '_reference')
        return '<Proxy for <%s>>' % (reference.repr())

    def __str__(self):
        reference = object.__getattribute__(self, '_reference')
        return reference.str()

class ProxyFactory(object):
    def __new__(self, reference):
        __logger__.debug('creating Proxy for %r', reference)

        class Proxy(ProxyBase):
            _reference = reference

            def methodWrapperFactory(method):
                def methodWrapper(self, *args, **kwargs):
                    return object.__getattribute__(ProxyBase, '__getattribute__')(self, method)(*args, **kwargs)
                return methodWrapper

            for method in reference.special_methods:
                if method in ['__new__', '__init__', '__del__', '__getattribute__',  # object instantiation breaks the proxy
                              '__call__', # because we have our own implementation that callse obj() directly
                              '__dir__', '__repr__', '__str__' # again, own implementations to dir(), repr() and str()
                             ]:
                    continue
                __logger__.debug('   - implementing %r', method)
                locals()[method] = methodWrapperFactory(method)

            del methodWrapperFactory

        return Proxy()

class RemoteException(Exception):
    pass

class Reference(object):
    def __init__(self, connection, remoteId):
        self.connection = connection
        self.remoteId   = remoteId

        self._special_methods = None

    def __del__(self):
        self.connection.destroy(self.remoteId)

    @property
    def special_methods(self):
        if self._special_methods is None:
            self._load_special_methods()
        return self._special_methods

    def _load_special_methods(self):
        try:
            isreference, retval = self.get_attribute('__class__')  ; assert(isreference)
            isreference, retval = retval.get_attribute('__dict__') ; assert(isreference)
            isreference, retval = retval.get_attribute('iterkeys')     ; assert(isreference)
            isreference, retval = retval.call()                   ; assert(isreference)
            isreference, retval = retval.get_attribute('next'); assert(isreference)
            def walker():
                isreference, r = retval.call()
                assert(not isreference)
                yield r

            self._special_methods = [method for method in walker() if method.startswith(b'__') and method.endswith(b'__')]
        except RemoteException:
            self._special_methods = []

    def wrap(self, val):
        if isinstance(val, Reference):
            if val.connection == self.connection:
                return True, val.remoteId
            else:
                raise TypeError("Cannot transfer objects from different connections")
        elif isinstance(val, transferTypes):
            return False, val
        elif isinstance(val, tuple):
            return False, tuple(self.wrap(item) for item in val)
        else:
            raise TypeError("Cannot transfer objects that are not immutable (%s not in %r)" % (type(val), transferTypes,))

    def unwrap(self, isreference, val):
        if isreference:
            return isreference, Reference(self.connection, val)
        elif isinstance(val, tuple):
            return isreference, tuple(self.unwrap(item) for item in val)
        else:
            return isreference, val


    def wrapargs(self, args, kwargs):
        args = [self.wrap(arg) for arg in args]
        kwargs = dict((key, self.wrap(val)) for (key, val) in iteritems(kwargs))
        return args, kwargs

    def call(self, *args, **kwargs):
        args, kwargs = self.wrapargs(args, kwargs)
        isreference, retval = self.connection.call(self.remoteId, *args, **kwargs)
        return self.unwrap(isreference, retval)

    def get_attribute(self, attribute):
        isreference, retval = self.connection.get_attribute(self.remoteId, attribute)
        return self.unwrap(isreference, retval)

    def dir(self):
        return self.connection.dir(self.remoteId)

    def repr(self):
        return self.connection.repr(self.remoteId)

    def str(self):
        return self.connection.str(self.remoteId)

def logdecorator(fn):
    def inner(*args, **kwargs):
        try:
            retval = fn(*args, **kwargs)
        except Exception as e:
            __logger__.warning(e)
            raise
        __logger__.debug("%r(%r, %r) -> %r"%(fn, args, kwargs, retval))
        return retval
    return inner

class FauxConnection(object):
    def __init__(self):
        self.references = []

    def format(self, value):
        if isinstance(value, transferTypes):
            return False, value
        elif isinstance(value, tuple):
            return False, tuple(format(item) for item in value)
        else:
            self.references.append(value)
            return True, len(self.references) -1

    def unformat(self, isreference, value):
        if isreference:
            return self.references[value]
        else:
            if isinstance(value, tuple):
                return (self.unformat(*item) for item in value)
            else:
                return value

    def unwrap(self, args, kwargs):
        args = [self.unformat(isref, val) for (isref, val) in args]
        kwargs = dict((key, self.unformat(isref, val)) for \
                      (key, (isref, val)) in kwargs)
        return args, kwargs

    @logdecorator
    def get_global(self, name):
        try:
            value = globals()[name]
        except KeyError:
            value = getattr(builtins, name)
        return self.format(value)

    @logdecorator
    def call(self, what, *args, **kwargs):
        args, kwargs = self.unwrap(args, kwargs)
        return self.format(self.references[what](*args, **kwargs))

    @logdecorator
    def get_attribute(self, what, attribute):
        return self.format(getattr(self.references[what], attribute))

    def destroy(self, what):
        __logger__.debug('%r: destroying object %i (was: %r)' % (self, what, self.references[what]))
        self.references[what] = None

    @logdecorator
    def dir(self, what):
        return dir(self.references[what])

    @logdecorator
    def str(self, what):
        return str(self.references[what])

    @logdecorator
    def repr(self, what):
        return repr(self.references[what])
