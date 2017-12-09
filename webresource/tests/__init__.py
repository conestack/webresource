import unittest


class BaseTestCase(unittest.TestCase):

    def assertRaisesWithMessage(self, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.assertFail()
        except Exception as inst:
            self.assertEqual(inst.message, msg)


def test_suite():
    from webresource.tests import test_compiler
    from webresource.tests import test_resource

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(test_compiler))
    suite.addTest(unittest.findTestCases(test_resource))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(test_suite())
