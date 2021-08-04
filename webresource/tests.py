from collections import Counter
from webresource.api import ResourceConfig
from webresource.api import Resource
import shutil
import unittest
import webresource as wr


class TestWebresource(unittest.TestCase):

    def test_ResourceConfig(self):
        config = ResourceConfig()

        self.assertFalse(config.debug)
        config.debug = True
        self.assertTrue(config.debug)

        self.assertEqual(config._merge_dir, None)
        self.assertTrue(config.merge_dir.startswith('/tmp'))
        self.assertEqual(config.merge_dir, config._merge_dir)
        shutil.rmtree(config._merge_dir)

        config.merge_dir = '/tmp/foo'
        self.assertEqual(config._merge_dir, '/tmp/foo')
        self.assertEqual(config.merge_dir, '/tmp/foo')

        self.assertIsInstance(wr.config, ResourceConfig)

    def test_Resource(self):
        self.assertRaises(ValueError, Resource, 'resource')

        resource = Resource('resource', resource='res.ext')

        self.assertEqual(resource.name, 'resource')
        self.assertEqual(resource.depends, '')
        self.assertTrue(resource.directory.endswith('/webresource'))
        self.assertEqual(resource.path, '/')
        self.assertEqual(resource.resource, 'res.ext')
        self.assertEqual(resource.compressed, None)
        self.assertEqual(resource.mergeable, False)
        self.assertEqual(resource.include, True)
        self.assertTrue(resource._config is wr.config)
        self.assertEqual(
            repr(resource),
            '<Resource name="resource", depends="", path="/" mergeable=False>'
        )

        def include():
            return False

        resource = Resource('resource', resource='res.ext', include=include)
        self.assertFalse(resource.include)

        config = ResourceConfig()
        resource = Resource(
            'resource',
            directory='/dir',
            resource='res.ext',
            _config=config
        )
        self.assertEqual(resource.file_path, '/dir/res.ext')

        resource.compressed = 'res.min.ext'
        self.assertEqual(resource.file_path, '/dir/res.min.ext')

        config.debug = True
        self.assertEqual(resource.file_path, '/dir/res.ext')

        group = wr.ResourceGroup('group')
        resource = Resource('resource', resource='res.ext', group=group)
        self.assertTrue(group.members[0] is resource)

    def test_JSResource(self):
        js = wr.JSResource('js_res', resource='res.js')
        self.assertEqual(js._type, 'js')
        self.assertEqual(
            repr(js),
            '<JSResource name="js_res", depends="", path="/" mergeable=False>'
        )

    def test_CSSResource(self):
        css = wr.CSSResource('css_res', resource='res.css')
        self.assertEqual(css._type, 'css')
        self.assertEqual(
            repr(css),
            '<CSSResource name="css_res", depends="", path="/" mergeable=False>'
        )

    def test_ResourceGroup(self):
        group = wr.ResourceGroup('groupname')
        self.assertEqual(group.name, 'groupname')
        self.assertEqual(group.members, [])
        self.assertEqual(group.include, True)
        self.assertEqual(repr(group), '<ResourceGroup name="groupname">')

        def include():
            return False

        group = wr.ResourceGroup('groupname', include=include)
        self.assertFalse(group.include)

        res = wr.JSResource('name', resource='name.js')
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
        resource = Resource('name1', resource='res1.ext', depends='name2')
        err = wr.ResourceCircularDependencyError([resource])
        self.assertEqual(str(err),
            'Resources define circular dependencies: '
            '[<Resource name="name1", depends="name2", path="/" mergeable=False>]'
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


if __name__ == '__main__':
    unittest.main()
