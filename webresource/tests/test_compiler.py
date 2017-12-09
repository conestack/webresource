from webresource.compiler import compiler
from webresource.compiler import Compiler
from webresource.compiler import CompilerError
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
                def compile(self, res):
                    return 'compiled'

            self.assertEqual(compiler.get('test').__class__, TestCompiler)

            msg = 'No compiler registered by name inexistent'
            self.assertRaisesWithMessage(
                CompilerError, msg, compiler.get, 'inexistent')

    def test_Compiler(self):
        msg = (
            'Can\'t instantiate abstract class Compiler with abstract '
            'methods compile'
        )
        self.assertRaisesWithMessage(TypeError, msg, Compiler)

        class TestCompiler(Compiler):
            def compile(self, resource):
                return 'compiled'

        comp = TestCompiler()
        self.assertEqual(comp.compile(JSResource('A')), 'compiled')
