import unittest


def test_suite():
    from webresource.tests import test_resource
    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(test_resource))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(test_suite())
