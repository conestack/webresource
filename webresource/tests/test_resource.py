from collections import OrderedDict
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import RegistryError
from webresource.resource import Resource as ResourceBase
from webresource.resource import css_resource
from webresource.resource import js_resource
from webresource.resource import resource_registry
from webresource.tests import BaseTestCase
import logging
import mock


class Resource(ResourceBase):

    @property
    def registry(self):
        return dict()


class TestResource(BaseTestCase):

    def test_Resource__init__(self):
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

    def test_resource_registry__register(self):
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
                "Resource <Resource object, uid=uid, depends=[], source=None, "
                "target=None, compiler=None, prefix=/> gets overwritten with "
                "<Resource object, uid=uid, depends=['foo'], source=None, "
                "target=None, compiler=None, prefix=/>"
            )
            mock_info.assert_called_once_with(expected)

    def test_resource_registry__resolve(self):
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

    def test_resource_registry_register_js(self):
        res = CSSResource('A')
        msg = (
            '<CSSResource object, uid=A, depends=[], source=None, target=None, '
            'compiler=None, prefix=/> is no ``JSResource`` instance'
        )
        self.assertRaisesWithMessage(msg, resource_registry.register_js, res)

        with mock.patch.dict(resource_registry.js, {}, clear=True):
            res = JSResource('A')
            resource_registry.register_js(res)
            self.assertEqual(resource_registry.js, {'A': res})

        self.assertEqual(resource_registry.js, {})

    def test_resource_registry_resolve_js(self):
        with mock.patch.dict(resource_registry.js, {}, clear=True):
            a = JSResource('A', depends='B')
            resource_registry.register_js(a)
            b = JSResource('B')
            resource_registry.register_js(b)
            self.assertEqual(resource_registry.resolve_js(), [b, a])

        self.assertEqual(resource_registry.js, {})

    def test_resource_registry_register_css(self):
        res = JSResource('A')
        msg = (
            '<JSResource object, uid=A, depends=[], source=None, target=None, '
            'compiler=None, prefix=/> is no ``CSSResource`` instance'
        )
        self.assertRaisesWithMessage(msg, resource_registry.register_css, res)

        with mock.patch.dict(resource_registry.css, {}, clear=True):
            res = CSSResource('A')
            resource_registry.register_css(res)
            self.assertEqual(resource_registry.css, {'A': res})

        self.assertEqual(resource_registry.css, {})

    def test_resource_registry_resolve_css(self):
        with mock.patch.dict(resource_registry.css, {}, clear=True):
            a = CSSResource('A', depends='B')
            resource_registry.register_css(a)
            b = CSSResource('B')
            resource_registry.register_css(b)
            self.assertEqual(resource_registry.resolve_css(), [b, a])

        self.assertEqual(resource_registry.css, {})

    def test_js_resource(self):
        with mock.patch.dict(resource_registry.js, {}, clear=True):
            js_resource(
                'app_scripts',
                depends=None,
                source='assets/app.js',
                target='assets/app.min.js',
                compiler='slimit',
                prefix='/javascripts/'
            )
            res = resource_registry.resolve_js()
            self.assertEqual(len(res), 1)
            expected = (
                '<JSResource object, uid=app_scripts, depends=[], '
                'source=assets/app.js, target=assets/app.min.js, '
                'compiler=slimit, prefix=/javascripts/>'
            )
            self.assertEqual(expected, str(res[0]))

        self.assertEqual(resource_registry.js, {})

    def test_css_resource(self):
        with mock.patch.dict(resource_registry.css, {}, clear=True):
            css_resource(
                'app_styles',
                depends=None,
                source='assets/app.less',
                target='assets/app.css',
                compiler='lesscpy',
                prefix='/stylesheets/'
            )
            res = resource_registry.resolve_css()
            self.assertEqual(len(res), 1)
            expected = (
                '<CSSResource object, uid=app_styles, depends=[], '
                'source=assets/app.less, target=assets/app.css, '
                'compiler=lesscpy, prefix=/stylesheets/>'
            )
            self.assertEqual(expected, str(res[0]))

        self.assertEqual(resource_registry.css, {})
