from webresource.resources import Resource

import unittest
import webresource as wr


class TestResolver(unittest.TestCase):
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
        resolver = wr.ResourceResolver(
            [
                Resource(name='res', resource='res.ext'),
                Resource(name='res', resource='res.ext'),
            ]
        )
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


if __name__ == '__main__':
    unittest.main()
