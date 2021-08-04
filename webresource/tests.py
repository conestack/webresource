from webresource.api import Config
from webresource.api import Resource
import shutil
import unittest
import webresource as wr


class TestWebresource(unittest.TestCase):

    def test_Config(self):
        config = Config()

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

        self.assertIsInstance(wr.config, Config)

    def test_Resource(self):
        self.assertRaises(ValueError, Resource, 'resource')

        resource = Resource('resource', resource='res.ext')

        self.assertEqual(resource.name, 'resource')
        self.assertEqual(resource.depends, [])
        self.assertTrue(resource.directory.endswith('/webresource'))
        self.assertEqual(resource.path, '/')
        self.assertEqual(resource.resource, 'res.ext')
        self.assertEqual(resource.compressed, None)
        self.assertEqual(resource.mergeable, False)
        self.assertEqual(resource.include, True)
        self.assertTrue(resource._config is wr.config)

        resource = Resource('resource', resource='res.ext', depends='other')
        self.assertEqual(resource.depends, ['other'])

        resource = Resource('resource', resource='res.ext', depends=['a', 'b'])
        self.assertEqual(resource.depends, ['a', 'b'])

        config = Config()
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

        js = wr.JSResource('js_resource', resource='res.js')
        self.assertEqual(js._type, 'js')

        css = wr.CSSResource('css_resource', resource='res.css')
        self.assertEqual(css._type, 'css')


if __name__ == '__main__':
    unittest.main()
