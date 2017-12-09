from webresource.compiler import compiler
from webresource.compiler import Compiler
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.tests import BaseTestCase
import mock


class TestCompiler(BaseTestCase):

    def test_compiler(self):
        with mock.patch.dict(compiler._registry, {}, clear=True):
            err = None
            try:
                @compiler('invalid')
                class InvalidCompiler(object):
                    pass
            except ValueError as e:
                err = str(e)
            finally:
                expected = 'Given object is no Compiler deriving class'
                self.assertEqual(expected, err)

            @compiler('test')
            class TestCompiler(Compiler):
                pass

            self.assertEqual(compiler.get('test'), TestCompiler)
            self.assertEqual(compiler.get('inexistent'), None)

    def test_Compiler(self):
        msg = (
            'Can\'t instantiate abstract class Compiler with abstract '
            'methods compile'
        )
        self.assertRaisesWithMessage(msg, Compiler)

        class TestCompiler(Compiler):
            def compile(self, resource):
                return 'compiled'

        comp = TestCompiler()
        self.assertEqual(comp.compile(JSResource('A')), 'compiled')
