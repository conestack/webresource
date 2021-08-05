from collections import Counter
from webresource._api import Resource
from webresource._api import ResourceConfig
from webresource._api import ResourceMixin
import shutil
import unittest
import webresource as wr


class TestWebresource(unittest.TestCase):

    def test_ResourceConfig(self):
        config = ResourceConfig()
        self.assertIsInstance(wr.config, ResourceConfig)
        self.assertFalse(config.debug)

        config.debug = True
        self.assertTrue(config.debug)

    def test_ResourceMixin(self):
        mixin = ResourceMixin(True)
        self.assertEqual(mixin.include, True)

        def include():
            return False

        mixin = ResourceMixin(include)
        self.assertFalse(mixin.include)

    def test_Resource(self):
        self.assertRaises(ValueError, Resource, 'resource')

        resource = Resource('resource', resource='res.ext')
        self.assertIsInstance(resource, ResourceMixin)
        self.assertEqual(resource.name, 'resource')
        self.assertEqual(resource.depends, '')
        self.assertTrue(resource.directory.endswith('/webresource'))
        self.assertEqual(resource.path, '/')
        self.assertEqual(resource.resource, 'res.ext')
        self.assertEqual(resource.compressed, None)
        self.assertEqual(resource.crossorigin, None)
        self.assertEqual(resource.referrerpolicy, None)
        self.assertEqual(resource.type_, None)
        self.assertTrue(resource._config is wr.config)
        self.assertEqual(
            repr(resource),
            '<Resource name="resource", depends="", path="/">'
        )

        config = ResourceConfig()
        resource = Resource(
            'resource',
            directory='/dir',
            resource='res.ext',
            _config=config
        )
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertEqual(resource.file_path, '/dir/res.ext')

        resource.compressed = 'res.min.ext'
        self.assertEqual(resource.file_name, 'res.min.ext')
        self.assertEqual(resource.file_path, '/dir/res.min.ext')

        config.debug = True
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertEqual(resource.file_path, '/dir/res.ext')

        group = wr.ResourceGroup('group')
        resource = Resource('resource', resource='res.ext', group=group)
        self.assertTrue(group.members[0] is resource)

    def test_ScriptResource(self):
        script = wr.ScriptResource('js_res', resource='res.js')
        self.assertEqual(script.async_, None)
        self.assertEqual(script.defer, None)
        self.assertEqual(script.integrity, None)
        self.assertEqual(script.nomodule, None)
        self.assertEqual(
            repr(script),
            '<ScriptResource name="js_res", depends="", path="/">'
        )

    def test_LinkResource(self):
        link = wr.LinkResource('ln_res', resource='res.ext')
        self.assertEqual(link.hreflang, None)
        self.assertEqual(link.media, None)
        self.assertEqual(link.rel, None)
        self.assertEqual(link.sizes, None)
        self.assertEqual(link.title, None)
        self.assertEqual(
            repr(link),
            '<LinkResource name="ln_res", depends="", path="/">'
        )

    def test_StyleResource(self):
        style = wr.StyleResource('css_res', resource='res.css')
        self.assertIsInstance(style, wr.LinkResource)
        self.assertEqual(style.type_, 'text/css')
        self.assertEqual(style.media, 'all')
        self.assertEqual(style.rel, 'stylesheet')
        self.assertEqual(
            repr(style),
            '<StyleResource name="css_res", depends="", path="/">'
        )

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
            '[<Resource name="res1", depends="res2", path="/">]'
        )

    def test_ResourceMissingDependencyError(self):
        resource = Resource('res', resource='res.ext', depends='missing')
        err = wr.ResourceMissingDependencyError(resource)
        self.assertEqual(str(err),
            'Resource define missing dependency: '
            '<Resource name="res", depends="missing", path="/">'
        )

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

        res3._include = False
        self.assertEqual(resolver._flat_resources(), [res1, res2])

        res3._include = True
        group3._include = False
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

    def test_ResourceRenderer__js_tag(self):
        renderer = wr.ResourceRenderer(None)
        self.assertEqual(
            renderer._js_tag('/js/res.js'),
            '<script src="https://tld.org/js/res.js"></script>\n'
        )

    def test_ResourceRenderer__css_tag(self):
        renderer = wr.ResourceRenderer(None)
        self.assertEqual(renderer._css_tag('/css/res.css'), (
            '<link href="https://tld.org/css/res.css" '
            'rel="stylesheet" type="text/css" media="all">\n'
        ))
        self.assertEqual(renderer._css_tag('/css/res.css', media='print'), (
            '<link href="https://tld.org/css/res.css" '
            'rel="stylesheet" type="text/css" media="print">\n'
        ))

    def test_ResourceRenderer__hashed_name(self):
        renderer = wr.ResourceRenderer(None)
        self.assertEqual(
            renderer._hashed_name(['res1', 'res2'], 'ext'),
            '74d837be6666f7c2e24ec75bac34a798bdfd01d4d3550ac29b2a9392e7eef1e3.ext'
        )


if __name__ == '__main__':
    unittest.main()
