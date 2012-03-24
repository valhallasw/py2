Python 3->2 compatibility layer
===============================

This project tries to bridge the python2-3 gap by allowing you to access python2 modules from python3. The system starts a background python2 process (not yet implemented), and communicates over JSON-RPC.

Required packages
-----------------
* six (for both server and client)

Howto
-----
Basic example:

>>> sys.version
'3.1.3 (r313:86834, Dec  9 2011, 20:48:13) \n[GCC 4.5.2]'
>>> from py2 import py2
>>> py2.rimport('sys').version
b'2.6.5 (r265:79063, Apr 16 2010, 13:09:56) \n[GCC 4.4.3]'

note that the remote sys.version returns a bytes object, as it's a str in python2.


Example for a real-life python2-only library:

>>> py2.rimport('sys').path.append('/home/valhallasw/src/pywikipedia/trunk")
>>> wikipedia = py2.rimport('wikipedia')
>>> p = wikipedia.Page('nl', 'Gebruiker:Valhallasw')
>>> p.get()
'<!-- sjablonenzooi -->\n{{kleine letter|titel=valhallasw}}\n\n[[Gebruiker:Valhallasw-sokpopje|Botje]], [[Gebruiker:Valhallasw/toolserver/bot|Toolserverbot]]\n\n{{Babel|nl|en-4|fr-2|de-2}}\n\n{{prefixindextabel}}\n\n[[fr:Utilisateur:Valhallasw-bot]]\n[[nv:Choyoołʼįįhí:Valhallasw-bot]](test)'


Implementation details
----------------------

In the following, 'local' refers to the client (py3) side and 'remote' to the server (py2) side.

Builtins can be accessed using remote_import('__builtin__').

Only immutable objects are transferred over the connection; other objects on the server are sent as reference. They are a Proxy object on the local side, which means they can be used as normal objects: all functions (should) work correctly. This also means lists will /not/ be transferred (else .append() etc would not work correctly), but tuples will. You can instantiate a remote list using something like remote_import('__builtin__').list((1,2,3,4)).

Local objects are not Proxied to the remote side, so remote_import('__builtin__').list([1,2,3,4]) will /not/ work. However, you can do something like

>>> rlist = remote_import('__builtin__').list
>>> x = rlist((1,2,3,4))
>>> y = rlist((5,6,7,8))
>>> x.extend(y)

as the remote side already has the y object.

License
-------

Available under the MIT license. See LICENSE for details.
