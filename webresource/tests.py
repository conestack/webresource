from collections import Counter
from webresource._api import Resource
from webresource._api import ResourceConfig
from webresource._api import ResourceMixin
import shutil
import unittest
import webresource as wr


class TestWebresource(unittest.TestCase):

    def tearDown(self):
        wr.config.development = False

    def test_ResourceConfig(self):
        config = ResourceConfig()
        self.assertIsInstance(wr.config, ResourceConfig)
        self.assertFalse(config.development)

        config.development = True
        self.assertTrue(config.development)

    def test_ResourceMixin(self):
        mixin = ResourceMixin(name='name', path='path', include=True)
        self.assertEqual(mixin.name, 'name')
        self.assertEqual(mixin.path, 'path')
        self.assertEqual(mixin.include, True)

        def include():
            return False

        mixin = ResourceMixin(name='name', path='path', include=include)
        self.assertFalse(mixin.include)

        self.assertEqual(mixin.resolved_path, 'path')
        mixin.resolved_path = 'other'
        self.assertEqual(mixin.resolved_path, 'other')

    def test_Resource(self):
        self.assertRaises(ValueError, Resource, 'res')

        resource = Resource('res', resource='res.ext')
        self.assertIsInstance(resource, ResourceMixin)
        self.assertEqual(resource.name, 'res')
        self.assertEqual(resource.depends, '')
        self.assertTrue(resource.directory.endswith('/webresource'))
        self.assertEqual(resource.path, '')
        self.assertEqual(resource.resource, 'res.ext')
        self.assertEqual(resource.compressed, None)
        self.assertEqual(resource.crossorigin, None)
        self.assertEqual(resource.crossorigin, None)
        self.assertEqual(resource.referrerpolicy, None)
        self.assertEqual(resource.type_, None)
        self.assertEqual(
            repr(resource),
            '<Resource name="res", depends="">'
        )

        resource = Resource('res', directory='./dir', resource='res.ext')
        self.assertTrue(resource.directory.endswith('/webresource/dir'))

        resource = Resource('res', directory='./dir/../other', resource='res.ext')
        self.assertTrue(resource.directory.endswith('/webresource/other'))

        resource = Resource('res', directory='/dir', resource='res.ext')
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertEqual(resource.file_path, '/dir/res.ext')

        resource.compressed = 'res.min.ext'
        self.assertEqual(resource.file_name, 'res.min.ext')
        self.assertEqual(resource.file_path, '/dir/res.min.ext')

        wr.config.development = True
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertEqual(resource.file_path, '/dir/res.ext')
        wr.config.development = False

        group = wr.ResourceGroup('group')
        resource = Resource('res', resource='res.ext', group=group)
        self.assertTrue(group.members[0] is resource)

        rendered = resource._render_tag('tag', False, foo='bar', baz=None)
        self.assertEqual(rendered, u'<tag foo="bar" />')

        rendered = resource._render_tag('tag', True, foo='bar', baz=None)
        self.assertEqual(rendered, u'<tag foo="bar"></tag>')

        self.assertRaises(NotImplementedError, resource.render, '')

        resource = Resource('res', resource='res.ext')
        resource_url = resource.resource_url('https://tld.org/')
        self.assertEqual(resource_url, 'https://tld.org/res.ext')

        resource = Resource('res', resource='res.ext', path='/resources')
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource = Resource('res', resource='res.ext', path='resources')
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource.resolved_path = 'other'
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/other/res.ext')

        resource = Resource(
            'res',
            resource='res.ext',
            compressed='res.min',
            path='/resources'
        )
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.min')

        wr.config.development = True
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource = Resource('res', url='https://ext.org/res')
        resource_url = resource.resource_url('')
        self.assertEqual(resource_url, 'https://ext.org/res')

    def test_ScriptResource(self):
        script = wr.ScriptResource('js_res', resource='res.js')
        self.assertEqual(script.async_, None)
        self.assertEqual(script.defer, None)
        self.assertEqual(script.integrity, None)
        self.assertEqual(script.nomodule, None)
        self.assertEqual(
            repr(script),
            '<ScriptResource name="js_res", depends="">'
        )
        self.assertEqual(
            script.render('https://tld.org'),
            '<script src="https://tld.org/res.js"></script>'
        )
        script.type_ = 'module'
        self.assertEqual(
            script.render('https://tld.org'),
            '<script src="https://tld.org/res.js" type="module"></script>'
        )

    def test_LinkResource(self):
        link = wr.LinkResource('icon_res', resource='icon.png')
        self.assertEqual(link.hreflang, None)
        self.assertEqual(link.media, None)
        self.assertEqual(link.rel, None)
        self.assertEqual(link.sizes, None)
        self.assertEqual(link.title, None)
        self.assertEqual(
            repr(link),
            '<LinkResource name="icon_res", depends="">'
        )
        link.rel = 'icon'
        link.type_ = 'image/png'
        self.assertEqual(
            link.render('https://tld.org'),
            '<link href="https://tld.org/icon.png" rel="icon" type="image/png" />'
        )

    def test_StyleResource(self):
        style = wr.StyleResource('css_res', resource='res.css')
        self.assertIsInstance(style, wr.LinkResource)
        self.assertEqual(style.type_, 'text/css')
        self.assertEqual(style.media, 'all')
        self.assertEqual(style.rel, 'stylesheet')
        self.assertEqual(
            repr(style),
            '<StyleResource name="css_res", depends="">'
        )
        self.assertEqual(style.render('https://tld.org'), (
            '<link href="https://tld.org/res.css" media="all" '
                  'rel="stylesheet" type="text/css" />'
        ))

    def test_ResourceGroup(self):
        group = wr.ResourceGroup('groupname')
        self.assertIsInstance(group, ResourceMixin)
        self.assertEqual(group.name, 'groupname')
        self.assertEqual(group.members, [])
        self.assertEqual(repr(group), '<ResourceGroup name="groupname">')

        res = wr.ScriptResource('name', resource='name.js')
        group.add(res)
        other = wr.ResourceGroup('other')
        group.add(other)
        self.assertEqual(group.members, [res, other])
        self.assertRaises(ValueError, group.add, object())

    def test_ResourceConflictError(self):
        counter = Counter(['a', 'b', 'b', 'c', 'c'])
        err = wr.ResourceConflictError(counter)
        self.assertEqual(str(err), 'Conflicting resource names: [\'b\', \'c\']')

    def test_ResourceCircularDependencyError(self):
        resource = Resource('res1', resource='res1.ext', depends='res2')
        err = wr.ResourceCircularDependencyError([resource])
        self.assertEqual(str(err),
            'Resources define circular dependencies: '
            '[<Resource name="res1", depends="res2">]'
        )

    def test_ResourceMissingDependencyError(self):
        resource = Resource('res', resource='res.ext', depends='missing')
        err = wr.ResourceMissingDependencyError(resource)
        self.assertEqual(str(err),
            'Resource define missing dependency: '
            '<Resource name="res", depends="missing">'
        )

    def test_ResourceResolver__resolve_paths(self):
        res1 = Resource('res1', resource='res1.ext')
        res2 = Resource('res2', resource='res2.ext', path='path')

        resolver = wr.ResourceResolver([res1, res2])
        resolver._resolve_paths()
        self.assertEqual(res1.resolved_path, '')
        self.assertEqual(res2.resolved_path, 'path')

        group = wr.ResourceGroup('group')
        group.add(res1)
        group.add(res2)

        resolver = wr.ResourceResolver([group])
        resolver._resolve_paths()
        self.assertEqual(res1.resolved_path, '')
        self.assertEqual(res2.resolved_path, 'path')

        group.path = 'other'
        resolver._resolve_paths()
        self.assertEqual(res1.resolved_path, 'other')
        self.assertEqual(res2.resolved_path, 'other')

        group1 = wr.ResourceGroup('group1')

        group2 = wr.ResourceGroup('group2', path='group2', group=group1)
        res1 = Resource('res1', resource='res1.ext', group=group2)

        group3 = wr.ResourceGroup('group3', path='group3', group=group1)
        res2 = Resource('res2', resource='res2.ext', group=group3)

        resolver = wr.ResourceResolver([group1])
        resolver._resolve_paths()
        self.assertEqual(res1.resolved_path, 'group2')
        self.assertEqual(res2.resolved_path, 'group3')

        group1 = wr.ResourceGroup('group1', path='group1')

        group2 = wr.ResourceGroup('group2', group=group1)
        res1 = Resource('res1', resource='res1.ext', group=group2)
        res2 = Resource('res2', resource='res2.ext', path='path', group=group2)

        group3 = wr.ResourceGroup('group3', path='group3', group=group1)
        res3 = Resource('res3', resource='res3.ext', group=group3)

        resolver = wr.ResourceResolver([group1])
        resolver._resolve_paths()
        self.assertEqual(res1.resolved_path, 'group1')
        self.assertEqual(res2.resolved_path, 'group1')
        self.assertEqual(res3.resolved_path, 'group1')

    def test_ResourceResolver__flat_resources(self):
        self.assertRaises(ValueError, wr.ResourceResolver, object())

        res1 = Resource('res1', resource='res1.ext')
        resolver = wr.ResourceResolver(res1)
        self.assertEqual(resolver.members, [res1])
        self.assertEqual(resolver._flat_resources(), [res1])

        res2 = Resource('res2', resource='res2.ext')
        resolver = wr.ResourceResolver([res1, res2])
        self.assertEqual(resolver.members, [res1, res2])
        self.assertEqual(resolver._flat_resources(), [res1, res2])

        res3 = Resource('res3', resource='res3.ext')

        group1 = wr.ResourceGroup('group1')
        group1.add(res1)

        group2 = wr.ResourceGroup('group2')
        group2.add(res2)

        group3 = wr.ResourceGroup('group3')
        group3.add(res3)
        group3.add(group2)

        resolver = wr.ResourceResolver([group1, group3])
        self.assertEqual(resolver._flat_resources(), [res1, res3, res2])

        res3.include = False
        self.assertEqual(resolver._flat_resources(), [res1, res2])

        res3.include = True
        group3.include = False
        self.assertEqual(resolver._flat_resources(), [res1])

    def test_ResourceResolver_resolve(self):
        resolver = wr.ResourceResolver([
            Resource('res', resource='res.ext'),
            Resource('res', resource='res.ext')
        ])
        self.assertRaises(wr.ResourceConflictError, resolver.resolve)

        res1 = Resource('res1', resource='res1.ext', depends='res2')
        res2 = Resource('res2', resource='res2.ext', depends='res3')
        res3 = Resource('res3', resource='res3.ext')

        resolver = wr.ResourceResolver([res1, res2, res3])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        resolver = wr.ResourceResolver([res2, res1, res3])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        resolver = wr.ResourceResolver([res1, res3, res2])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        res1 = Resource('res1', resource='res1.ext', depends='res2')
        res2 = Resource('res2', resource='res2.ext', depends='res1')

        resolver = wr.ResourceResolver([res1, res2])
        self.assertRaises(wr.ResourceCircularDependencyError, resolver.resolve)

        res1 = Resource('res1', resource='res1.ext', depends='res2')
        res2 = Resource('res2', resource='res2.ext', depends='missing')

        resolver = wr.ResourceResolver([res1, res2])
        self.assertRaises(wr.ResourceMissingDependencyError, resolver.resolve)

    def test_ResourceRenderer(self):
        resources = wr.ResourceGroup('res', path='res')
        icon = wr.LinkResource(
            'icon',
            resource='icon.png',
            group=resources,
            rel='icon',
            type_='image/png'
        )
        style = wr.StyleResource('css', resource='styles.css', group=resources)
        external = wr.StyleResource(
            'ext_css',
            url='https://ext.org/styles.css',
            group=resources
        )
        script = wr.ScriptResource(
            'js',
            resource='script.js',
            compressed='script.min.js',
            group=resources
        )
        resolver = wr.ResourceResolver(resources)
        renderer = wr.ResourceRenderer(resolver, base_url='https://example.com')

        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://example.com/res/icon.png" '
                  'rel="icon" type="image/png" />\n'
            '<link href="https://example.com/res/styles.css" media="all" '
                  'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
                  'rel="stylesheet" type="text/css" />\n'
            '<script src="https://example.com/res/script.min.js"></script>'
        ))

        wr.config.development = True
        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://example.com/res/icon.png" '
                  'rel="icon" type="image/png" />\n'
            '<link href="https://example.com/res/styles.css" media="all" '
                  'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
                  'rel="stylesheet" type="text/css" />\n'
            '<script src="https://example.com/res/script.js"></script>'
        ))


if __name__ == '__main__':
    unittest.main()
