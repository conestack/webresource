from collections import OrderedDict
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import RegistryError
from webresource.resource import Resource as ResourceBase
from webresource.resource import css_resource
from webresource.resource import js_resource
from webresource.resource import resource_registry as rr
from webresource.tests import BaseTestCase
import logging
import mock
import unittest


class Resource(ResourceBase):
    registry = dict()


class TestResource(BaseTestCase):

    def test___init__(self):
        r = Resource('uid')
        self.assertEqual(r.uid, 'uid')
        self.assertEqual(r.depends, [])
        self.assertEqual(r.source, None)
        self.assertEqual(r.source_dir, None)
        self.assertEqual(r.target, None)
        self.assertEqual(r.compiler, None)
        self.assertEqual(r.compiler_opts, None)
        self.assertEqual(r.prefix, '/')

        r = Resource('uid', depends='foo')
        self.assertEqual(r.depends, ['foo'])

        r = Resource('uid', depends=['foo', 'bar'])
        self.assertEqual(r.depends, ['foo', 'bar'])

        r = Resource('uid', depends=('foo', 'bar'))
        self.assertEqual(r.depends, ('foo', 'bar'))

    def test_registry(self):
        r = Resource('uid')
        self.assertEqual(r.registry, {})

    def test_source_path(self):
        r = Resource('uid', source='assets/resource', source_dir='/some/path')
        self.assertEqual(r.source_path, '/some/path/assets/resource')

    def test_target_path(self):
        # no target defined, target_path is source_path
        r = Resource('uid', source='assets/resource', source_dir='/some/path')
        self.assertEqual(r.target_path, '/some/path/assets/resource')

        # target defined, as base for target source_dir is used
        r.target = 'assets/resource.compiled'
        self.assertEqual(r.target_path, '/some/path/assets/resource.compiled')

        # target points to dependency resource
        with mock.patch.dict(Resource.registry, {}, clear=True):
            reg = Resource.registry
            a = reg['A'] = Resource(
                'A', source='a', source_dir='/path', target='a.compiled')
            b = reg['B'] = Resource(
                'B', depends='A', source='b', source_dir='/path',
                target='uid:A')
            self.assertEqual(b.target_path, '/path/a.compiled')

            b.target = 'uid:a'
            msg = 'Dependency resource a not exists'
            self.assertRaisesWithMessage(
                RegistryError, msg, lambda: b.target_path)

        self.assertEqual(Resource.registry, {})


class TestResourceRegistry(BaseTestCase):

    def test__register(self):
        logger = logging.getLogger('webresource')
        with mock.patch.object(logger, 'info') as mock_info:
            reg = dict()

            res = Resource('uid')
            rr._register(reg, res)
            self.assertEqual(reg, {'uid': res})

            res = Resource('uid', depends=['foo'])
            rr._register(reg, res)
            self.assertEqual(reg, {'uid': res})

            expected = (
                "Resource <Resource object, uid=uid, depends=[], source=None, "
                "target=None, compiler=None, prefix=/> gets overwritten with "
                "<Resource object, uid=uid, depends=['foo'], source=None, "
                "target=None, compiler=None, prefix=/>"
            )
            mock_info.assert_called_once_with(expected)

    def test__resolve(self):
        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='A')
        res = rr._resolve(reg)
        self.assertEqual(res, [a, b])

        reg = OrderedDict()
        b = reg['B'] = Resource('B', depends='A')
        a = reg['A'] = Resource('A')
        res = rr._resolve(reg)
        self.assertEqual(res, [a, b])

        reg = OrderedDict()
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        c = reg['C'] = Resource('C')
        b = reg['B'] = Resource('B', depends='A')
        a = reg['A'] = Resource('A')
        res = rr._resolve(reg)
        self.assertEqual(res, [c, a, b, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='A')
        c = reg['C'] = Resource('C')
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        res = rr._resolve(reg)
        self.assertEqual(res, [a, b, c, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends=['A', 'C'])
        c = reg['C'] = Resource('C')
        d = reg['D'] = Resource('D', depends=['B', 'C'])
        res = rr._resolve(reg)
        self.assertEqual(res, [a, c, b, d])

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends='C')
        msg = 'Dependency resource C not exists'
        self.assertRaisesWithMessage(RegistryError, msg, rr._resolve, reg)

        reg = OrderedDict()
        a = reg['A'] = Resource('A')
        b = reg['B'] = Resource('B', depends=['A', 'C'])
        c = reg['C'] = Resource('C', depends=['A', 'B'])
        msg = 'Circular dependency B - C'
        self.assertRaisesWithMessage(RegistryError, msg, rr._resolve, reg)

    def test_register_js(self):
        res = CSSResource('A')
        msg = (
            '<CSSResource object, uid=A, depends=[], source=None, target=None, '
            'compiler=None, prefix=/> is no ``JSResource`` instance'
        )
        self.assertRaisesWithMessage(ValueError, msg, rr.register_js, res)

        with mock.patch.dict(rr.js, {}, clear=True):
            res = JSResource('A')
            rr.register_js(res)
            self.assertEqual(rr.js, {'A': res})

        self.assertEqual(rr.js, {})

    def test_resolve_js(self):
        with mock.patch.dict(rr.js, {}, clear=True):
            a = JSResource('A', depends='B')
            rr.register_js(a)
            b = JSResource('B')
            rr.register_js(b)
            self.assertEqual(rr.resolve_js(), [b, a])

        self.assertEqual(rr.js, {})

    def test_register_css(self):
        res = JSResource('A')
        msg = (
            '<JSResource object, uid=A, depends=[], source=None, target=None, '
            'compiler=None, prefix=/> is no ``CSSResource`` instance'
        )
        self.assertRaisesWithMessage(ValueError, msg, rr.register_css, res)

        with mock.patch.dict(rr.css, {}, clear=True):
            res = CSSResource('A')
            rr.register_css(res)
            self.assertEqual(rr.css, {'A': res})

        self.assertEqual(rr.css, {})

    def test_resolve_css(self):
        with mock.patch.dict(rr.css, {}, clear=True):
            a = CSSResource('A', depends='B')
            rr.register_css(a)
            b = CSSResource('B')
            rr.register_css(b)
            self.assertEqual(rr.resolve_css(), [b, a])

        self.assertEqual(rr.css, {})


class TestRegisterFunctions(unittest.TestCase):

    def test_js_resource(self):
        with mock.patch.dict(rr.js, {}, clear=True):
            js_resource(
                'app_scripts',
                depends=None,
                source='assets/app.js',
                target='assets/app.min.js',
                compiler='slimit',
                prefix='/javascripts/'
            )
            res = rr.resolve_js()
            self.assertEqual(len(res), 1)
            expected = (
                '<JSResource object, uid=app_scripts, depends=[], '
                'source=assets/app.js, target=assets/app.min.js, '
                'compiler=slimit, prefix=/javascripts/>'
            )
            self.assertEqual(expected, str(res[0]))

        self.assertEqual(rr.js, {})

    def test_css_resource(self):
        with mock.patch.dict(rr.css, {}, clear=True):
            css_resource(
                'app_styles',
                depends=None,
                source='assets/app.less',
                target='assets/app.css',
                compiler='lesscpy',
                prefix='/stylesheets/'
            )
            res = rr.resolve_css()
            self.assertEqual(len(res), 1)
            expected = (
                '<CSSResource object, uid=app_styles, depends=[], '
                'source=assets/app.less, target=assets/app.css, '
                'compiler=lesscpy, prefix=/stylesheets/>'
            )
            self.assertEqual(expected, str(res[0]))

        self.assertEqual(rr.css, {})
