import random
import unittest

from cbor2 import CBOREncoder, CBORDecoder
from io import BytesIO

from golem.core.simpleserializer import SimpleSerializerDebug, SimpleSerializerRelease, SimpleSerializer, CBORSerializer, \
    CBORCoder


class Example:
    def __init__(self):
        self.int = 4
        self.string = u"abcdefghi\\kwa \\bla"
        self.list = ['a', 'b', 'c']
        self.dict = {'k': None, 'w': 1.0, 'a': 'bla'}

    def __eq__(self, exm2):
        if self.int != exm2.int:
            return False
        if self.string != exm2.string:
            return False
        if self.list != exm2.list:
            return False
        if cmp(self.dict, exm2.dict) != 0:
            return False
        return True


class TestSimpleSerializer(unittest.TestCase):
    def testSerializer(self):
        self.assertTrue(isinstance(SimpleSerializer(), CBORSerializer))


class TestSimpleSerializerDebug(unittest.TestCase):
    def testSerializer(self):
        data = ['foo', {'bar': ('baz', None, 1.0, 2)}]
        ser = SimpleSerializerDebug.dumps(data)
        self.assertTrue(isinstance(ser, str))
        data2 = SimpleSerializerDebug.loads(ser)
        self.assertTrue(isinstance(data2, list))
        self.assertEqual(len(data2), len(data))


class TestSimpleSerializerRelease(unittest.TestCase):
    def testSerializer(self):
        data = Example()
        ser = SimpleSerializerRelease.dumps(data)
        self.assertTrue(isinstance(ser, str))
        data2 = SimpleSerializerRelease.loads(ser)
        self.assertTrue(isinstance(data2, Example))
        self.assertEqual(data, data2)


class MockSerializationInnerSubject(object):
    def __init__(self):
        self.property_1 = random.randrange(1, 1 * 10 ** 18)
        self._property_2 = True
        self.property_3 = "string"
        self.property_4 = ['list', 'of', ('items',)]

    def method(self):
        pass


class MockSerializationSubject(object):
    def __init__(self):
        self.property_1 = dict(k='v')
        self.property_2 = MockSerializationInnerSubject()
        self._property_3 = None

    def method_1(self):
        pass

    def _method_2(self):
        pass


class TestCBORSerializer(unittest.TestCase):

    def testConversion(self):
        obj = MockSerializationSubject()
        dict_repr = CBORCoder._object_to_dict(obj)

        assert 'property_1' in dict_repr
        assert 'property_2' in dict_repr
        assert '_property_3' not in dict_repr
        assert 'method_1' not in dict_repr
        assert '_method_2' not in dict_repr

        reconstructed = CBORCoder._dict_to_object(dict_repr)

        assert reconstructed.__class__ == obj.__class__
        assert reconstructed.property_2.__class__ == MockSerializationInnerSubject

        inner = reconstructed.property_2

        assert inner.property_1
        assert inner.property_1 == obj.property_2.property_1
        assert isinstance(inner.property_3, basestring)
        assert isinstance(inner.property_4, list)
        assert '_property_2' not in inner.__dict__

    def testSerialization(self):
        obj = MockSerializationSubject()

        decoders = CBORSerializer.decoders
        encoders = CBORSerializer.encoders

        # encode
        buf = BytesIO()
        CBOREncoder(encoders=encoders).encode(obj, buf)
        serialized = buf.getvalue()

        # decode
        buf = BytesIO(serialized)
        decoder = CBORDecoder(semantic_decoders=decoders)
        deserialized = decoder.decode(buf)

        assert deserialized.__class__ == obj.__class__
        assert CBORSerializer.loads(CBORSerializer.dumps(obj)).__class__ == obj.__class__
