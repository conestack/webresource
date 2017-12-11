from contextlib import contextmanager
from webresource.compiler import compiler
from webresource.compiler import Compiler
from webresource.compiler import CompilerError
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import css_resource
from webresource.resource import js_resource
from webresource.resource import resource_registry as rr
from webresource.tests import BaseTestCase
import mock
import shutil
import tempfile


@contextmanager
def tempdir():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


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
                def compile_resource(self, res):
                    return 'compiled'

            self.assertEqual(compiler.get('test').__class__, TestCompiler)

            msg = 'No compiler registered by name inexistent'
            self.assertRaisesWithMessage(
                CompilerError, msg, compiler.get, 'inexistent')

    def test_Compiler(self):
        msg = (
            'Can\'t instantiate abstract class Compiler with abstract '
            'methods compile_resource'
        )
        self.assertRaisesWithMessage(TypeError, msg, Compiler)

        class TestCompiler(Compiler):
            def compile_resource(self, resource):
                return 'compiled'

        cpl = TestCompiler()
        self.assertEqual(cpl.compile_resource(JSResource('A')), 'compiled')

    def test_DefaultCompiler(self):
        cpl = compiler.get('default')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js'
                )
                with open(rr.js['a'].source_path, 'w') as f:
                    f.write('var foo=1;\nconsole.log(foo);')
                compiled = cpl.compile_resource(rr.js['a'])
                self.assertEqual(compiled, 'var foo=1;\nconsole.log(foo);')

    def test_SlimitCompiler(self):
        cpl = compiler.get('slimit')
        self.assertTrue(cpl.mangle)
        self.assertTrue(cpl.mangle_toplevel)

        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    target='a.js.min',
                    compiler='slimit'
                )
                with open(rr.js['a'].source_path, 'w') as f:
                    f.write('var foo=1;\nconsole.log(foo);')
                compiled = cpl.compile_resource(rr.js['a'])
                self.assertEqual(compiled, 'var a=1;console.log(a);')

    def test_LesscpyCompiler(self):
        cpl = compiler.get('lesscpy')
        self.assertTrue(cpl.minify)

        with mock.patch.dict(rr.css, {}, clear=True):
            with tempdir() as path:
                css_resource(
                    'a',
                    resource_dir=path,
                    source='a.less',
                    target='a.css',
                    compiler='lesscpy'
                )
                with open(rr.css['a'].source_path, 'w') as f:
                    f.write('a { border-width: 2px * 3; }')
                compiled = cpl.compile_resource(rr.css['a'])
                self.assertEqual(compiled, 'a{border-width:6px;}')
