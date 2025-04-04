# -*- coding: utf-8 -*-
from collections import Counter
from webresource._api import (
    is_py3,
    LinkMixin,
    Resource,
    ResourceConfig,
    ResourceMixin
)
import os
import shutil
import tempfile
import unittest
import webresource as wr


try:
    FileNotFoundError
except NameError:  # pragma: nocover
    FileNotFoundError = EnvironmentError


def temp_directory(fn):
    def wrapper(*a, **kw):
        tempdir = tempfile.mkdtemp()
        kw['tempdir'] = tempdir
        try:
            fn(*a, **kw)
        finally:
            shutil.rmtree(tempdir)
    return wrapper


def np(path):
    """Normalize path."""
    return path.replace('/', os.path.sep)


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
        mixin = ResourceMixin(
            name='name', path='path', include=True
        )
        self.assertEqual(mixin.name, 'name')
        self.assertEqual(mixin.path, 'path')
        self.assertEqual(mixin.include, True)
        self.assertEqual(mixin.directory, None)
        self.assertEqual(mixin.parent, None)

        mixin.parent = ResourceMixin(name='other', path='other')
        mixin.path = None
        self.assertEqual(mixin.path, 'other')

        mixin.parent.parent = ResourceMixin(name='root', path='root')
        mixin.parent.path = None
        self.assertEqual(mixin.path, 'root')

        mixin.directory = '/dir'
        self.assertTrue(mixin.directory.endswith(os.path.join(os.path.sep, 'dir')))

        mixin.directory = '/resources/dir/../other'
        self.assertTrue(mixin.directory.endswith(np('/resources/other')))

        mixin.parent = ResourceMixin(name='other', directory='/other')
        mixin.directory = None
        self.assertTrue(mixin.directory.endswith(os.path.join(os.path.sep, 'other')))

        mixin.parent.parent = ResourceMixin(name='root', directory='/root')
        mixin.parent.directory = None
        self.assertTrue(mixin.directory.endswith(os.path.join(os.path.sep, 'root')))

        def include():
            return False

        mixin = ResourceMixin(name='name', path='path', include=include)
        self.assertFalse(mixin.include)

        self.assertFalse(mixin.copy() is mixin)

    @temp_directory
    def test_Resource(self, tempdir):
        self.assertRaises(wr.ResourceError, Resource, 'res')

        resource = Resource(name='res', resource='res.ext')
        self.assertIsInstance(resource, ResourceMixin)
        self.assertEqual(resource.name, 'res')
        self.assertEqual(resource.depends, None)
        self.assertEqual(resource.directory, None)
        self.assertEqual(resource.path, None)
        self.assertEqual(resource.resource, 'res.ext')
        self.assertEqual(resource.compressed, None)
        self.assertEqual(resource.include, True)
        self.assertEqual(resource.unique, False)
        self.assertEqual(resource.unique_prefix, '++webresource++')
        self.assertEqual(resource.hash_algorithm, 'sha384')
        self.assertEqual(resource.url, None)
        self.assertEqual(resource.crossorigin, None)
        self.assertEqual(resource.referrerpolicy, None)
        self.assertEqual(resource.type_, None)
        self.assertEqual(
            repr(resource),
            'Resource name="res", depends="None"'
        )

        resource = Resource(name='res', resource='res.ext')
        self.assertEqual(resource.file_name, 'res.ext')
        with self.assertRaises(wr.ResourceError):
            resource.file_path

        resource = Resource(name='res', directory='/dir', resource='res.ext')
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertTrue(resource.file_path.endswith(np('/dir/res.ext')))

        resource.compressed = 'res.min.ext'
        self.assertEqual(resource.file_name, 'res.min.ext')
        self.assertTrue(resource.file_path.endswith(np('/dir/res.min.ext')))

        wr.config.development = True
        self.assertEqual(resource.file_name, 'res.ext')
        self.assertTrue(resource.file_path.endswith(np('/dir/res.ext')))
        wr.config.development = False

        group = wr.ResourceGroup(name='group')
        resource = Resource(name='res', resource='res.ext', group=group)
        self.assertTrue(group.members[0] is resource)

        rendered = resource._render_tag('tag', False, foo='bar', baz=None)
        self.assertEqual(rendered, u'<tag foo="bar" />')

        rendered = resource._render_tag('tag', True, foo='bar', baz=None)
        self.assertEqual(rendered, u'<tag foo="bar"></tag>')

        self.assertRaises(NotImplementedError, resource.render, '')

        resource = Resource(name='res', resource='res.ext')
        resource_url = resource.resource_url('https://tld.org/')
        self.assertEqual(resource_url, 'https://tld.org/res.ext')

        resource = Resource(name='res', resource='res.ext', path='/resources')
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource = Resource(name='res', resource='res.ext', path='resources')
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource = Resource(
            name='res',
            resource='res.ext',
            compressed='res.min',
            path='/resources'
        )
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.min')

        wr.config.development = True
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/resources/res.ext')

        resource = Resource(name='res', url='https://ext.org/res')
        resource_url = resource.resource_url('')
        self.assertEqual(resource_url, 'https://ext.org/res')

        wr.config.development = False
        with open(os.path.join(tempdir, 'res'), 'wb') as f:
            f.write(u'Resource Content ä'.encode('utf8'))

        resource = Resource(name='res', resource='res', directory=tempdir)
        self.assertEqual(resource.file_data, b'Resource Content \xc3\xa4')

        hash_ = (
            'VwEVpw/Hy4OlSeTX7oDQ/lzkncnWgKEV'
            '0zOX9OXa9Uy+qypLkrBrJxPtNsax1HJo'
        )
        self.assertEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/res')

        unique_key = resource.unique_key
        self.assertEqual(
            unique_key,
            '++webresource++4be37419-d3f6-5ec5-99e8-92565ede87d0'
        )

        resource.unique = True
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(
            resource_url,
            'https://tld.org/{}/res'.format(unique_key)
        )

        with open(os.path.join(tempdir, 'res'), 'w') as f:
            f.write('Changed Content')

        self.assertEqual(resource.file_data, b'Changed Content')
        self.assertEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(
            resource_url,
            'https://tld.org/{}/res'.format(unique_key)
        )

        wr.config.development = True
        self.assertNotEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertNotEqual(
            resource_url,
            'https://tld.org/{}/res'.format(unique_key)
        )

        resource = Resource(
            name='res',
            resource='res.ext',
            custom_attr='value'
        )
        self.assertEqual(resource.additional_attrs, dict(custom_attr='value'))

    @temp_directory
    def test_ScriptResource(self, tempdir):
        script = wr.ScriptResource(name='js_res', resource='res.js')
        self.assertEqual(script.async_, None)
        self.assertEqual(script.defer, None)
        self.assertEqual(script.integrity, None)
        self.assertEqual(script.nomodule, None)
        self.assertEqual(
            repr(script),
            'ScriptResource name="js_res", depends="None"'
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

        script.url = 'https://ext.org/script.js'
        self.assertRaises(wr.ResourceError, setattr, script, 'integrity', True)

        script.integrity = 'sha384-ABC'
        self.assertEqual(script.integrity, 'sha384-ABC')

        with open(os.path.join(tempdir, 'script.js'), 'w') as f:
            f.write('Script Content')

        script = wr.ScriptResource(
            name='script',
            resource='script.js',
            directory=tempdir,
            integrity=True
        )
        hash_ = 'omjyXfsb+ti/5fpn4QjjSYjpKRnxWpzc6rIUE6mXxyDjbLS9AotgsLWQZtylXicX'
        self.assertEqual(script.file_hash, hash_)
        self.assertEqual(script.integrity, 'sha384-{}'.format(hash_))

        rendered = script.render('https://tld.org')
        expected = 'integrity="sha384-{}"'.format(hash_)
        self.assertTrue(rendered.find(expected))

        with open(os.path.join(tempdir, 'script.js'), 'w') as f:
            f.write('Changed Script')

        self.assertEqual(script.integrity, 'sha384-{}'.format(hash_))

        wr.config.development = True
        self.assertNotEqual(script.integrity, 'sha384-{}'.format(hash_))

        script = wr.ScriptResource(
            name='js_res',
            resource='res.js',
            custom='value'
        )
        self.assertEqual(
            script.render('https://tld.org'),
            '<script custom="value" src="https://tld.org/res.js"></script>'
        )

    def test_LinkMixin(self):
        link = LinkMixin(name='link_res', resource='resource.md')
        self.assertEqual(link.hreflang, None)
        self.assertEqual(link.media, None)
        self.assertEqual(link.rel, None)
        self.assertEqual(link.sizes, None)
        self.assertEqual(link.title, None)
        self.assertEqual(
            repr(link),
            'LinkMixin name="link_res", depends="None"'
        )
        link.hreflang = 'en'
        link.media = 'screen'
        link.rel = 'alternate'
        link.type_ = 'text/markdown'
        self.assertEqual(link.render('https://tld.org'), (
            '<link href="https://tld.org/resource.md" hreflang="en" '
            'media="screen" rel="alternate" type="text/markdown" />'
        ))

        link = LinkMixin(
            name='link_res',
            resource='resource.md',
            custom='value'
        )
        self.assertEqual(
            link.render('https://tld.org'),
            '<link custom="value" href="https://tld.org/resource.md" />'
        )

    def test_LinkResource(self):
        link = wr.LinkResource(name='icon_res', resource='icon.png')
        self.assertIsInstance(link, LinkMixin)
        self.assertEqual(
            repr(link),
            'LinkResource name="icon_res", depends="None"'
        )
        link.rel = 'icon'
        link.type_ = 'image/png'
        link.sizes = '16x16'
        self.assertEqual(link.render('https://tld.org'), (
            '<link href="https://tld.org/icon.png" rel="icon" '
            'sizes="16x16" type="image/png" />'
        ))

        link = wr.LinkResource(
            name='icon_res',
            resource='icon.png',
            custom='value'
        )
        self.assertEqual(
            link.render('https://tld.org'),
            '<link custom="value" href="https://tld.org/icon.png" />'
        )

    def test_StyleResource(self):
        style = wr.StyleResource(name='css_res', resource='res.css')
        self.assertIsInstance(style, LinkMixin)
        self.assertEqual(style.type_, 'text/css')
        self.assertEqual(style.media, 'all')
        self.assertEqual(style.rel, 'stylesheet')
        self.assertEqual(
            repr(style),
            'StyleResource name="css_res", depends="None"'
        )
        self.assertEqual(style.render('https://tld.org'), (
            '<link href="https://tld.org/res.css" media="all" '
            'rel="stylesheet" type="text/css" />'
        ))

        style = wr.StyleResource(
            name='css_res',
            resource='res.css',
            custom='value'
        )
        self.assertEqual(style.render('https://tld.org'), (
            '<link custom="value" href="https://tld.org/res.css" media="all" '
            'rel="stylesheet" type="text/css" />'
        ))

    def test_ResourceGroup(self):
        group = wr.ResourceGroup(name='groupname')
        self.assertIsInstance(group, ResourceMixin)
        self.assertEqual(group.name, 'groupname')
        self.assertEqual(group.members, [])
        self.assertEqual(repr(group), 'ResourceGroup name="groupname"')

        res = wr.ScriptResource(name='name', resource='name.js')
        group.add(res)
        other = wr.ResourceGroup(name='other')
        group.add(other)
        self.assertEqual(group.members, [res, other])
        self.assertRaises(wr.ResourceError, group.add, object())

        root_group = wr.ResourceGroup(name='root')
        member_group = wr.ResourceGroup(name='member', group=root_group)
        member_res = wr.ScriptResource(
            name='res',
            resource='res.js',
            group=member_group
        )
        self.assertTrue(member_group.parent is root_group)
        self.assertTrue(member_res.parent is member_group)

        group = wr.ResourceGroup(
            name='groupname',
            path='group_path',
            directory='/path/to/dir')
        group.add(wr.ResourceGroup(name='group1'))
        wr.ResourceGroup(name='group2', group=group)

        self.assertEqual(group.path, group.members[0].path)
        self.assertEqual(group.path, group.members[1].path)
        self.assertEqual(group.directory, group.members[0].directory)
        self.assertEqual(group.directory, group.members[1].directory)

        root = wr.ResourceGroup(name='root')
        wr.StyleResource(name='root-style', resource='root.css', group=root)
        wr.ScriptResource(name='root-script', resource='root.js', group=root)
        wr.LinkResource(name='root-link', resource='root.link', group=root)

        group = wr.ResourceGroup(name='group', group=root)
        wr.StyleResource(name='group-style', resource='group.css', group=group)
        wr.ScriptResource(name='group-script', resource='group.js', group=group)
        wr.LinkResource(name='group-link', resource='group.link', group=group)

        self.assertEqual(
            sorted([res.name for res in root.scripts]),
            ['group-script', 'root-script']
        )
        self.assertEqual(
            sorted([res.name for res in root.styles]),
            ['group-style', 'root-style']
        )
        self.assertEqual(
            sorted([res.name for res in root.links]),
            ['group-link', 'root-link']
        )

        resource = wr.Resource(resource='res')
        with self.assertRaises(wr.ResourceError):
            resource.remove()

        group = wr.ResourceGroup()
        resource = wr.Resource(resource='res', group=group)
        self.assertEqual(group.members, [resource])
        resource.remove()
        self.assertEqual(group.members, [])
        self.assertEqual(resource.parent, None)

    def test_ResourceConflictError(self):
        counter = Counter(['a', 'b', 'b', 'c', 'c'])
        err = wr.ResourceConflictError(counter)
        self.assertEqual(str(err), 'Conflicting resource names: [\'b\', \'c\']')

    def test_ResourceCircularDependencyError(self):
        resource = Resource(name='res1', resource='res1.ext', depends='res2')
        err = wr.ResourceCircularDependencyError([resource])
        self.assertEqual(str(err), (
            'Resources define circular dependencies: '
            '[Resource name="res1", depends="[\'res2\']"]'
        ))

    def test_ResourceMissingDependencyError(self):
        resource = Resource(name='res', resource='res.ext', depends='missing')
        err = wr.ResourceMissingDependencyError(resource)
        self.assertEqual(str(err), (
            'Resource defines missing dependency: '
            'Resource name="res", depends="[\'missing\']"'
        ))

    def test_ResourceResolver__flat_resources(self):
        self.assertRaises(wr.ResourceError, wr.ResourceResolver, object())

        res1 = Resource(name='res1', resource='res1.ext')
        resolver = wr.ResourceResolver(res1)
        self.assertEqual(resolver.members, [res1])
        self.assertEqual(resolver._flat_resources(), [res1])

        res2 = Resource(name='res2', resource='res2.ext')
        resolver = wr.ResourceResolver([res1, res2])
        self.assertEqual(resolver.members, [res1, res2])
        self.assertEqual(resolver._flat_resources(), [res1, res2])

        res3 = Resource(name='res3', resource='res3.ext')

        group1 = wr.ResourceGroup(name='group1')
        group1.add(res1)

        group2 = wr.ResourceGroup(name='group2')
        group2.add(res2)

        group3 = wr.ResourceGroup(name='group3')
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
            Resource(name='res', resource='res.ext'),
            Resource(name='res', resource='res.ext')
        ])
        self.assertRaises(wr.ResourceConflictError, resolver.resolve)

        res1 = Resource(name='res1', resource='res1.ext', depends='res2')
        res2 = Resource(name='res2', resource='res2.ext', depends='res3')
        res3 = Resource(name='res3', resource='res3.ext')

        resolver = wr.ResourceResolver([res1, res2, res3])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        resolver = wr.ResourceResolver([res2, res1, res3])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        resolver = wr.ResourceResolver([res1, res3, res2])
        self.assertEqual(resolver.resolve(), [res3, res2, res1])

        res1 = Resource(name='res1', resource='res1.ext', depends='res2')
        res2 = Resource(name='res2', resource='res2.ext', depends='res1')

        resolver = wr.ResourceResolver([res1, res2])
        self.assertRaises(wr.ResourceCircularDependencyError, resolver.resolve)

        res1 = Resource(name='res1', resource='res1.ext', depends='res2')
        res2 = Resource(name='res2', resource='res2.ext', depends='missing')

        resolver = wr.ResourceResolver([res1, res2])
        self.assertRaises(wr.ResourceMissingDependencyError, resolver.resolve)

        res1 = Resource(name='res1', resource='res1.ext', depends=['res2', 'res4'])
        res2 = Resource(name='res2', resource='res2.ext', depends=['res3', 'res4'])
        res3 = Resource(name='res3', resource='res3.ext', depends=['res4', 'res5'])
        res4 = Resource(name='res4', resource='res4.ext', depends='res5')
        res5 = Resource(name='res5', resource='res5.ext')

        resolver = wr.ResourceResolver([res1, res2, res3, res4, res5])
        self.assertEqual(resolver.resolve(), [res5, res4, res3, res2, res1])

        resolver = wr.ResourceResolver([res5, res4, res3, res2, res1])
        self.assertEqual(resolver.resolve(), [res5, res4, res3, res2, res1])

        resolver = wr.ResourceResolver([res4, res5, res2, res3, res1])
        self.assertEqual(resolver.resolve(), [res5, res4, res3, res2, res1])

        resolver = wr.ResourceResolver([res1, res3, res2, res5, res4])
        self.assertEqual(resolver.resolve(), [res5, res4, res3, res2, res1])

        res1 = Resource(name='res1', resource='res1.ext', depends=['res2', 'res3'])
        res2 = Resource(name='res2', resource='res2.ext', depends=['res1', 'res3'])
        res3 = Resource(name='res3', resource='res3.ext', depends=['res1', 'res2'])

        resolver = wr.ResourceResolver([res1, res2, res3])
        self.assertRaises(wr.ResourceCircularDependencyError, resolver.resolve)

        res1 = Resource(name='res1', resource='res1.ext', depends=['res2', 'res3'])
        res2 = Resource(name='res2', resource='res2.ext', depends=['res1', 'res3'])
        res3 = Resource(name='res3', resource='res3.ext', depends=['res1', 'res4'])

        resolver = wr.ResourceResolver([res1, res2, res3])
        self.assertRaises(wr.ResourceMissingDependencyError, resolver.resolve)

    def test_ResourceRenderer(self):
        resources = wr.ResourceGroup('res', path='res')
        wr.LinkResource(
            name='icon',
            resource='icon.png',
            group=resources,
            rel='icon',
            type_='image/png'
        )
        wr.StyleResource(name='css', resource='styles.css', group=resources)
        wr.StyleResource(
            name='ext_css',
            url='https://ext.org/styles.css',
            group=resources
        )
        wr.ScriptResource(
            name='js',
            resource='script.js',
            compressed='script.min.js',
            group=resources
        )
        resolver = wr.ResourceResolver(resources)
        renderer = wr.ResourceRenderer(resolver, base_url='https://tld.org')

        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://tld.org/res/icon.png" '
            'rel="icon" type="image/png" />\n'
            '<link href="https://tld.org/res/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<script src="https://tld.org/res/script.min.js"></script>'
        ))

        wr.config.development = True
        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://tld.org/res/icon.png" '
            'rel="icon" type="image/png" />\n'
            '<link href="https://tld.org/res/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<script src="https://tld.org/res/script.js"></script>'
        ))

        # check if unique raises on render b/c file does not exist.
        wr.ScriptResource(
            name='js2',
            directory='',
            resource='script2.js',
            compressed='script2.min.js',
            group=resources,
            unique=True,
        )
        with self.assertRaises(FileNotFoundError):
            renderer.render()

    def test_GracefulResourceRenderer(self):
        resources = wr.ResourceGroup('res', path='res')
        wr.LinkResource(
            name='icon',
            resource='icon.png',
            group=resources,
            rel='icon',
            type_='image/png',
        )
        wr.StyleResource(name='css', resource='styles.css', group=resources)
        wr.StyleResource(
            name='ext_css',
            url='https://ext.org/styles.css',
            group=resources,
        )
        wr.ScriptResource(
            name='js',
            resource='script.js',
            compressed='script.min.js',
            group=resources,
        )
        resolver = wr.ResourceResolver(resources)
        renderer = wr.GracefulResourceRenderer(
            resolver,
            base_url='https://tld.org',
        )
        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://tld.org/res/icon.png" '
            'rel="icon" type="image/png" />\n'
            '<link href="https://tld.org/res/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<script src="https://tld.org/res/script.min.js"></script>'
        ))

        wr.config.development = True
        rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://tld.org/res/icon.png" '
            'rel="icon" type="image/png" />\n'
            '<link href="https://tld.org/res/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<script src="https://tld.org/res/script.js"></script>'
        ))
        # check if unique raises on is catched on render and turned into
        wr.ScriptResource(
            name='js2',
            directory='',
            resource='script2.js',
            compressed='script2.min.js',
            group=resources,
            depends="js",
            unique=True,
        )
        if is_py3:  # pragma: nocover
            with self.assertLogs() as captured:
                rendered = renderer.render()
                # check that there is only one log message
                self.assertEqual(len(captured.records), 1)
                # check if its ours
                self.assertEqual(
                    captured.records[0].getMessage().split('\n')[0],
                    'Failure to render resource "js2"',
                )
        else:  # pragma: nocover
            rendered = renderer.render()
        self.assertEqual(rendered, (
            '<link href="https://tld.org/res/icon.png" '
            'rel="icon" type="image/png" />\n'
            '<link href="https://tld.org/res/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<link href="https://ext.org/styles.css" media="all" '
            'rel="stylesheet" type="text/css" />\n'
            '<script src="https://tld.org/res/script.js"></script>\n'
            '<!-- Failure to render resource "js2" - details in logs -->'
        ))


if __name__ == '__main__':
    unittest.main()
