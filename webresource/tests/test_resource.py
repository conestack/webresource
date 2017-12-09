from collections import OrderedDict
from webresource.resource import RegistryError
from webresource.resource import Resource
from webresource.resource import resource_registry
import logging
import mock
import unittest


class TestResource(unittest.TestCase):

    def assertRaisesWithMessage(self, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.assertFail()
        except Exception as inst:
            self.assertEqual(inst.message, msg)

    def test_Resource__init__(self):
        r = Resource('uid')
        self.assertEqual(r.uid, 'uid')
        self.assertEqual(r.depends, [])

        r = Resource('uid', depends='foo')
        self.assertEqual(r.depends, ['foo'])

        r = Resource('uid', depends=['foo', 'bar'])
        self.assertEqual(r.depends, ['foo', 'bar'])

        r = Resource('uid', depends=('foo', 'bar'))
        self.assertEqual(r.depends, ('foo', 'bar'))

    def test_Resource_register(self):
        logger = logging.getLogger('webresource')
        with mock.patch.object(logger, 'info') as mock_info:
            reg = dict()

            res = Resource('uid')
            resource_registry._register(reg, res)
            self.assertEqual(reg, {'uid': res})

            res = Resource('uid', depends=['foo'])
            resource_registry._register(reg, res)
            self.assertEqual(reg, {'uid': res})

            expected = (
                "Resource <Resource object, uid=uid, depends=[]> gets "
                "overwritten with <Resource object, uid=uid, depends=['foo']>"
            )
            mock_info.assert_called_once_with(expected)

    def test_Resource_resolve(self):
        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='A')
        res = resource_registry._resolve(reg)
        self.assertEqual(res, [a, b])

        reg = OrderedDict()
        b = reg['B'] = Resource('B', depends='A')
        a = reg['A'] = Resource('A')
        res = resource_registry._resolve(reg)
        self.assertEqual(res, [a, b])

        reg = OrderedDict()
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        c = reg['C'] = Resource('C')
        b = reg['B'] = Resource('B', depends='A')
        a = reg['A'] = Resource('A')
        res = resource_registry._resolve(reg)
        self.assertEqual(res, [c, a, b, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='A')
        c = reg['C'] = Resource('C')
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        res = resource_registry._resolve(reg)
        self.assertEqual(res, [a, b, c, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends=['A', 'C'])
        c = reg['C'] = Resource('C')
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        res = resource_registry._resolve(reg)
        self.assertEqual(res, [a, c, b, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='C')
        msg = 'Dependency resource C not exists'
        self.assertRaisesWithMessage(msg, resource_registry._resolve, reg)

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends=['A', 'C'])
        c = reg['C'] = Resource('C', depends=['A', 'B'])
        msg = 'Circular dependency B - C'
        self.assertRaisesWithMessage(msg, resource_registry._resolve, reg)
