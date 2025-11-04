# -*- coding: utf-8 -*-
"""Tests for webresource.base module."""
import os
import unittest
from webresource.base import ResourceMixin
from tests.test_utils import np


class TestBase(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
