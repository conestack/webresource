from contextlib import contextmanager
from webresource.compiler import compiler
from webresource.compiler import compiler_context
from webresource.compiler import Compiler
from webresource.compiler import CompilerError
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import css_resource
from webresource.resource import js_resource
from webresource.resource import resource_registry as rr
from webresource.tests import BaseTestCase
import mock
import os
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

    def test_compiler_context(self):
        msg = 'Invalid call to ``fd`` outside compiler run'
        self.assertRaisesWithMessage(
            CompilerError, msg, compiler_context.fd, '/path')

        msg = 'Invalid call to ``paths`` outside compiler run'
        self.assertRaisesWithMessage(
            CompilerError, msg, compiler_context.paths)

        with tempdir() as dirpath:
            path = os.path.join(dirpath, 'resource')
            with compiler_context() as cc:
                fd = cc.fd(path)

                self.assertTrue(fd is cc.fd(path))
                self.assertTrue(fd is compiler_context.fd(path))
                self.assertEqual({path: fd}, cc.data.fds)

                paths = cc.paths()
                self.assertEqual(paths, [path])

        msg = "'thread._local' object has no attribute 'fds'"
        self.assertRaisesWithMessage(
            AttributeError, msg, lambda: compiler_context.data.fds)

        msg = 'Invalid call to ``fd`` outside compiler run'
        self.assertRaisesWithMessage(
            CompilerError, msg, compiler_context.fd, '/path')

        msg = 'Invalid call to ``paths`` outside compiler run'
        self.assertRaisesWithMessage(
            CompilerError, msg, compiler_context.paths)

        msg = 'I/O operation on closed file'
        self.assertRaisesWithMessage(ValueError, msg, fd.write, '')

    def test_Compiler(self):
        msg = (
            'Can\'t instantiate abstract class Compiler with abstract '
            'methods compile_resource'
        )
        self.assertRaisesWithMessage(TypeError, msg, Compiler)

        class TestCompiler(Compiler):
            def compile_resource(self, resource):
                pass

        cpl = TestCompiler()
        self.assertFalse(cpl.compile_required)
        self.assertEqual(cpl.compile_resource(JSResource('A')), None)
        self.assertEqual(cpl.post_compile(), None)


class TestDefaultCompiler(BaseTestCase):

    def test_target_equals_source(self):
        cpl = compiler.get('default')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js'
                )
                with open(res.source_path, 'w') as f:
                    f.write('var foo=1;\nconsole.log(foo);')
                with compiler_context():
                    cpl.compile_resource(res)
                self.assertEqual(
                    os.listdir(path),
                    ['a.js']
                )

    def test_target_differs_source(self):
        cpl = compiler.get('default')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    target='b.js'
                )
                with open(res.source_path, 'w') as f:
                    f.write('var foo=1;\nconsole.log(foo);')
                with compiler_context():
                    cpl.compile_resource(res)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.js', 'b.js']
                )
                with open(res.target_path, 'r') as f:
                    self.assertEqual(f.read(), 'var foo=1;\nconsole.log(foo);')

    def test_target_is_dependency_resource(self):
        cpl = compiler.get('default')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res_a = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    target='bundle.js'
                )
                res_b = js_resource(
                    'b',
                    resource_dir=path,
                    source='b.js',
                    target='uid:a'
                )
                with open(res_a.source_path, 'w') as f:
                    f.write('var a=1;\n')
                with open(res_b.source_path, 'w') as f:
                    f.write('var b=1;\n')
                with compiler_context():
                    cpl.compile_resource(res_a)
                    cpl.compile_resource(res_b)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.js', 'b.js', 'bundle.js']
                )
                with open(os.path.join(path, 'bundle.js'), 'r') as f:
                    self.assertEqual(f.read(), 'var a=1;\nvar b=1;\n')


class TestSlimitCompiler(BaseTestCase):

    def test_compiler_opts(self):
        cpl = compiler.get('slimit')
        self.assertFalse(cpl.mangle)
        self.assertFalse(cpl.mangle_toplevel)

    def test_target_equals_source(self):
        cpl = compiler.get('slimit')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    compiler='slimit'
                )
                with compiler_context():
                    msg = ('Compilation target must differ from source to '
                           'avoid override')
                    self.assertRaisesWithMessage(
                        CompilerError, msg, cpl.compile_resource, res)

    def test_target_differs_source(self):
        cpl = compiler.get('slimit')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    target='a.min.js',
                    compiler='slimit',
                    compiler_opts={
                        'mangle': True,
                        'mangle_toplevel': True
                    }
                )
                with open(res.source_path, 'w') as f:
                    f.write('var foo=1;\nconsole.log(foo);')
                with compiler_context():
                    cpl.compile_resource(res)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.js', 'a.min.js']
                )
                with open(res.target_path, 'r') as f:
                    self.assertEqual(f.read(), 'var a=1;console.log(a);')

    def test_target_is_dependency_resource(self):
        cpl = compiler.get('slimit')
        with mock.patch.dict(rr.js, {}, clear=True):
            with tempdir() as path:
                res_a = js_resource(
                    'a',
                    resource_dir=path,
                    source='a.js',
                    target='bundle.js',
                    compiler='slimit'
                )
                res_b = js_resource(
                    'b',
                    resource_dir=path,
                    source='b.js',
                    target='uid:a',
                    compiler='slimit'
                )
                with open(res_a.source_path, 'w') as f:
                    f.write('var a=1;\n')
                with open(res_b.source_path, 'w') as f:
                    f.write('var b=1;\n')
                with compiler_context():
                    cpl.compile_resource(res_a)
                    cpl.compile_resource(res_b)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.js', 'b.js', 'bundle.js']
                )
                with open(os.path.join(path, 'bundle.js'), 'r') as f:
                    self.assertEqual(f.read(), 'var a=1;var b=1;')


class TestLesscpyCompiler(BaseTestCase):

    def test_compiler_opts(self):
        cpl = compiler.get('lesscpy')
        self.assertTrue(cpl.minify)

    def test_target_equals_source(self):
        cpl = compiler.get('lesscpy')
        with mock.patch.dict(rr.css, {}, clear=True):
            with tempdir() as path:
                res = css_resource(
                    'a',
                    resource_dir=path,
                    source='a.less',
                    compiler='lesscpy'
                )
                with compiler_context():
                    msg = ('Compilation target must differ from source to '
                           'avoid override')
                    self.assertRaisesWithMessage(
                        CompilerError, msg, cpl.compile_resource, res)

    def test_target_differs_source(self):
        cpl = compiler.get('lesscpy')
        with mock.patch.dict(rr.css, {}, clear=True):
            with tempdir() as path:
                res = css_resource(
                    'a',
                    resource_dir=path,
                    source='a.less',
                    target='a.css',
                    compiler='lesscpy',
                    compiler_opts={
                        'minify': False
                    }
                )
                with open(res.source_path, 'w') as f:
                    f.write('a { border-width: 2px * 3; }')
                with compiler_context():
                    cpl.compile_resource(res)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.css', 'a.less']
                )
                with open(res.target_path, 'r') as f:
                    self.assertEqual(f.read(), 'a {\n border-width: 6px;\n}')

    def test_target_is_dependency_resource(self):
        cpl = compiler.get('lesscpy')
        with mock.patch.dict(rr.css, {}, clear=True):
            with tempdir() as path:
                res_a = css_resource(
                    'a',
                    resource_dir=path,
                    source='a.less',
                    target='bundle.css',
                    compiler='lesscpy'
                )
                res_b = css_resource(
                    'b',
                    resource_dir=path,
                    source='b.less',
                    target='uid:a',
                    compiler='lesscpy'
                )
                with open(res_a.source_path, 'w') as f:
                    f.write('a { border-width: 2px * 3; }')
                with open(res_b.source_path, 'w') as f:
                    f.write('b { border-width: 2px * 5; }')
                with compiler_context():
                    cpl.compile_resource(res_a)
                    cpl.compile_resource(res_b)
                self.assertEqual(
                    sorted(os.listdir(path)),
                    ['a.less', 'b.less', 'bundle.css']
                )
                with open(os.path.join(path, 'bundle.css'), 'r') as f:
                    self.assertEqual(
                        f.read(),
                        'a{border-width:6px;}b{border-width:10px;}'
                    )
