from tests.test_utils import np
from tests.test_utils import temp_directory
from webresource.base import ResourceMixin
from webresource.resources import LinkMixin
from webresource.resources import Resource

import os
import unittest
import webresource as wr


class TestResources(unittest.TestCase):
    def tearDown(self):
        wr.config.development = False

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
        self.assertEqual(repr(resource), 'Resource name="res", depends="None"')

        resource = Resource(name='res', url='http://tld.net/resource')
        with self.assertRaises(wr.ResourceError):
            resource.file_name

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
        self.assertEqual(rendered, '<tag foo="bar" />')

        rendered = resource._render_tag('tag', True, foo='bar', baz=None)
        self.assertEqual(rendered, '<tag foo="bar"></tag>')

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
            name='res', resource='res.ext', compressed='res.min', path='/resources'
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
            f.write('Resource Content ä'.encode())

        resource = Resource(name='res', resource='res', directory=tempdir)
        self.assertEqual(resource.file_data, b'Resource Content \xc3\xa4')

        hash_ = 'VwEVpw/Hy4OlSeTX7oDQ/lzkncnWgKEV0zOX9OXa9Uy+qypLkrBrJxPtNsax1HJo'
        self.assertEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, 'https://tld.org/res')

        unique_key = resource.unique_key
        self.assertEqual(
            unique_key, '++webresource++4be37419-d3f6-5ec5-99e8-92565ede87d0'
        )

        resource.unique = True
        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, f'https://tld.org/{unique_key}/res')

        with open(os.path.join(tempdir, 'res'), 'w') as f:
            f.write('Changed Content')

        self.assertEqual(resource.file_data, b'Changed Content')
        self.assertEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertEqual(resource_url, f'https://tld.org/{unique_key}/res')

        wr.config.development = True
        self.assertNotEqual(resource.file_hash, hash_)

        resource_url = resource.resource_url('https://tld.org')
        self.assertNotEqual(resource_url, f'https://tld.org/{unique_key}/res')

        resource = Resource(name='res', resource='res.ext', custom_attr='value')
        self.assertEqual(resource.additional_attrs, dict(custom_attr='value'))

    @temp_directory
    def test_ScriptResource(self, tempdir):
        script = wr.ScriptResource(name='js_res', resource='res.js')
        self.assertEqual(script.async_, None)
        self.assertEqual(script.defer, None)
        self.assertEqual(script.integrity, None)
        self.assertEqual(script.nomodule, None)
        self.assertEqual(repr(script), 'ScriptResource name="js_res", depends="None"')
        self.assertEqual(
            script.render('https://tld.org'),
            '<script src="https://tld.org/res.js"></script>',
        )
        script.type_ = 'module'
        self.assertEqual(
            script.render('https://tld.org'),
            '<script src="https://tld.org/res.js" type="module"></script>',
        )

        script.url = 'https://ext.org/script.js'
        self.assertRaises(wr.ResourceError, setattr, script, 'integrity', True)

        script.integrity = 'sha384-ABC'
        self.assertEqual(script.integrity, 'sha384-ABC')

        with open(os.path.join(tempdir, 'script.js'), 'w') as f:
            f.write('Script Content')

        script = wr.ScriptResource(
            name='script', resource='script.js', directory=tempdir, integrity=True
        )
        hash_ = 'omjyXfsb+ti/5fpn4QjjSYjpKRnxWpzc6rIUE6mXxyDjbLS9AotgsLWQZtylXicX'
        self.assertEqual(script.file_hash, hash_)
        self.assertEqual(script.integrity, f'sha384-{hash_}')

        rendered = script.render('https://tld.org')
        expected = f'integrity="sha384-{hash_}"'
        self.assertTrue(rendered.find(expected))

        with open(os.path.join(tempdir, 'script.js'), 'w') as f:
            f.write('Changed Script')

        self.assertEqual(script.integrity, f'sha384-{hash_}')

        wr.config.development = True
        self.assertNotEqual(script.integrity, f'sha384-{hash_}')

        script = wr.ScriptResource(name='js_res', resource='res.js', custom='value')
        self.assertEqual(
            script.render('https://tld.org'),
            '<script custom="value" src="https://tld.org/res.js"></script>',
        )

    def test_LinkMixin(self):
        link = LinkMixin(name='link_res', resource='resource.md')
        self.assertEqual(link.hreflang, None)
        self.assertEqual(link.media, None)
        self.assertEqual(link.rel, None)
        self.assertEqual(link.sizes, None)
        self.assertEqual(link.title, None)
        self.assertEqual(repr(link), 'LinkMixin name="link_res", depends="None"')
        link.hreflang = 'en'
        link.media = 'screen'
        link.rel = 'alternate'
        link.type_ = 'text/markdown'
        self.assertEqual(
            link.render('https://tld.org'),
            (
                '<link href="https://tld.org/resource.md" hreflang="en" '
                'media="screen" rel="alternate" type="text/markdown" />'
            ),
        )

        link = LinkMixin(name='link_res', resource='resource.md', custom='value')
        self.assertEqual(
            link.render('https://tld.org'),
            '<link custom="value" href="https://tld.org/resource.md" />',
        )

    def test_LinkResource(self):
        link = wr.LinkResource(name='icon_res', resource='icon.png')
        self.assertIsInstance(link, LinkMixin)
        self.assertEqual(repr(link), 'LinkResource name="icon_res", depends="None"')
        link.rel = 'icon'
        link.type_ = 'image/png'
        link.sizes = '16x16'
        self.assertEqual(
            link.render('https://tld.org'),
            (
                '<link href="https://tld.org/icon.png" rel="icon" '
                'sizes="16x16" type="image/png" />'
            ),
        )

        link = wr.LinkResource(name='icon_res', resource='icon.png', custom='value')
        self.assertEqual(
            link.render('https://tld.org'),
            '<link custom="value" href="https://tld.org/icon.png" />',
        )

    def test_StyleResource(self):
        style = wr.StyleResource(name='css_res', resource='res.css')
        self.assertIsInstance(style, LinkMixin)
        self.assertEqual(style.type_, 'text/css')
        self.assertEqual(style.media, 'all')
        self.assertEqual(style.rel, 'stylesheet')
        self.assertEqual(repr(style), 'StyleResource name="css_res", depends="None"')
        self.assertEqual(
            style.render('https://tld.org'),
            (
                '<link href="https://tld.org/res.css" media="all" '
                'rel="stylesheet" type="text/css" />'
            ),
        )

        style = wr.StyleResource(name='css_res', resource='res.css', custom='value')
        self.assertEqual(
            style.render('https://tld.org'),
            (
                '<link custom="value" href="https://tld.org/res.css" media="all" '
                'rel="stylesheet" type="text/css" />'
            ),
        )


if __name__ == '__main__':
    unittest.main()
