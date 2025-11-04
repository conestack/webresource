# -*- coding: utf-8 -*-
"""Tests for webresource.renderer module."""
import unittest
import webresource as wr


class TestRenderer(unittest.TestCase):

    def tearDown(self):
        wr.config.development = False

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
        with self.assertLogs() as captured:
            rendered = renderer.render()
            # check that there is only one log message
            self.assertEqual(len(captured.records), 1)
            # check if its ours
            self.assertEqual(
                captured.records[0].getMessage().split('\n')[0],
                'Failure to render resource "js2"',
            )
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
