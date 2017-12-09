from webresource.resource import Resource
from webresource.resource import resource_registry
import logging
import mock
import unittest


class TestResource(unittest.TestCase):

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
