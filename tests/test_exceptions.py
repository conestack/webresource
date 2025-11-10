from collections import Counter
from webresource.resources import Resource

import unittest
import webresource as wr


class TestExceptions(unittest.TestCase):
    def test_ResourceConflictError(self):
        counter = Counter(['a', 'b', 'b', 'c', 'c'])
        err = wr.ResourceConflictError(counter)
        self.assertEqual(str(err), "Conflicting resource names: ['b', 'c']")

    def test_ResourceCircularDependencyError(self):
        resource = Resource(name='res1', resource='res1.ext', depends='res2')
        err = wr.ResourceCircularDependencyError([resource])
        self.assertEqual(
            str(err),
            (
                'Resources define circular dependencies: '
                '[Resource name="res1", depends="[\'res2\']"]'
            ),
        )

    def test_ResourceMissingDependencyError(self):
        resource = Resource(name='res', resource='res.ext', depends='missing')
        err = wr.ResourceMissingDependencyError(resource)
        self.assertEqual(
            str(err),
            (
                'Resource defines missing dependency: '
                'Resource name="res", depends="[\'missing\']"'
            ),
        )


if __name__ == '__main__':
    unittest.main()
