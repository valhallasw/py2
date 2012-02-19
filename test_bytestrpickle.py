# -*- coding: utf-8 -*-
import unittest
from unittest import TestCase

import io
import pickle

from bytestrpickle import BytestrPickler, BytestrUnpickler

class BytestrUnpicklerTests(TestCase):
    def unpickleEqual(self, data, unpickled):
        self.assertEqual(
            BytestrUnpickler(io.BytesIO(data)).load(),
            unpickled)

    def test_str_protocol_0(self):
        """ Test str from protocol=0
        python 2: pickle.dumps('bytestring \x00\xa0', protocol=0) """
        self.unpickleEqual(
                b"S'bytestring \\x00\\xa0'\np0\n.",
                b'bytestring \x00\xa0')

    def test_str_protocol_1(self):
        """ Test str from protocol=1
        python 2: pickle.dumps('bytestring \x00\xa0', protocol=1) """
        self.unpickleEqual(
                b'U\rbytestring \x00\xa0q\x00.',
                b'bytestring \x00\xa0')

    def test_str_protocol_2(self):
        """ Test str from protocol=2
        python 2: pickle.dumps('bytestring \x00\xa0', protocol=2) """
        self.unpickleEqual(
                b'\x80\x02U\rbytestring \x00\xa0q\x00.',
                b'bytestring \x00\xa0')

    def test_unicode_protocol_0(self):
        """ Test unicode with protocol=0
        python 2: pickle.dumps(u"Компьютер", protocol=0) """
        self.unpickleEqual(
                b'V\\u041a\\u043e\\u043c\\u043f\\u044c\\u044e\\u0442\\u0435\\u0440\np0\n.',
                'Компьютер')

    def test_unicode_protocol_1(self):
        """ Test unicode with protocol=1
        python 2: pickle.dumps(u"Компьютер", protocol=1) """
        self.unpickleEqual(
                b'X\x12\x00\x00\x00\xd0\x9a\xd0\xbe\xd0\xbc\xd0\xbf\xd1\x8c\xd1\x8e\xd1\x82\xd0\xb5\xd1\x80q\x00.',
                'Компьютер')

    def test_unicode_protocol_2(self):
        """ Test unicode with protocol=1
        python 2: pickle.dumps(u"Компьютер", protocol=2) """
        self.unpickleEqual(
                b'\x80\x02X\x12\x00\x00\x00\xd0\x9a\xd0\xbe\xd0\xbc\xd0\xbf\xd1\x8c\xd1\x8e\xd1\x82\xd0\xb5\xd1\x80q\x00.',
                'Компьютер')

    def test_long_str_protocol_1(self):
        """ Test long str with protocol=1
        python 2: pickle.dumps('x'*300, protocol=1) """
        self.unpickleEqual(
                b'T,\x01\x00\x00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxq\x00.',
                b'x'*300)


class BytestrPicklerTests(TestCase):
    def pickleEqual(self, data, pickled, protocol):
        f = io.BytesIO()
        BytestrPickler(f, protocol=protocol).dump(data)
        self.assertEqual(f.getvalue(), pickled)

    def test_str_protocol_0(self):
        self.pickleEqual(
                b'bytestring \x00\xa0',
                b"S'bytestring \\x00\\xa0'\np0\n.",
                0)

    def test_str_protocol_1(self):
        self.pickleEqual(
                b'bytestring \x00\xa0',
                b'U\rbytestring \x00\xa0q\x00.',
                1)

    def test_str_protocol_2(self):
        self.pickleEqual(
                b'bytestring \x00\xa0',
                b'\x80\x02U\rbytestring \x00\xa0q\x00.',
                2)

    def test_bytes_protocol_3(self):
        self.pickleEqual(
                b'bytestring \x00\xa0',
                pickle.dumps(b'bytestring \x00\xa0'),
                3)


class RoundtripTest(TestCase):
    def roundtripEqual(self, data, protocol):
        f = io.BytesIO()
        BytestrPickler(f, protocol=protocol).dump(data)
        self.assertEqual(
                BytestrUnpickler(io.BytesIO(f.getvalue())).load(),
                data)

    testcases = {'bytestring': b'bytestring \x00\xa0',
                 'ru_computer_utf': 'Компьютер'.encode('utf-8'),
                 'longstring': b'a'*300,
                 'ru_computer_unicode': 'Компьютер'}

    for name, value in testcases.items():
        for protocol in range(4):
            locals()['test_%s_protocol_%i' % (name, protocol)] = (lambda value, protocol: lambda self: self.roundtripEqual(value, protocol))(value, protocol)
                 

if __name__ == '__main__':
    unittest.main()
