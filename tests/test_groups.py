from webresource.base import ResourceMixin

import unittest
import webresource as wr


class TestGroups(unittest.TestCase):
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
            name='res', resource='res.js', group=member_group
        )
        self.assertTrue(member_group.parent is root_group)
        self.assertTrue(member_res.parent is member_group)

        group = wr.ResourceGroup(
            name='groupname', path='group_path', directory='/path/to/dir'
        )
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
            sorted([res.name for res in root.scripts]), ['group-script', 'root-script']
        )
        self.assertEqual(
            sorted([res.name for res in root.styles]), ['group-style', 'root-style']
        )
        self.assertEqual(
            sorted([res.name for res in root.links]), ['group-link', 'root-link']
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


if __name__ == '__main__':
    unittest.main()
