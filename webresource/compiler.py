from webresource.compat import add_metaclass
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import resource_registry as rr
import abc
import os
import threading
import time


class compiler(object):
    """Compiler decorator and registry.
    """

    _registry = dict()
    """Registry for available compilers.
    """

    _instances = dict()
    """Container for compiler instances.
    """

    def __init__(self, name):
        """Initialize compiler registration call.

        :param name: Compiler name.
        """
        self.name = name

    def __call__(self, compiler):
        """Register compiler by name.

        :param compiler: Compiler deriving class.
        :return object: Return passed compiler class.
        """
        if not issubclass(compiler, Compiler):
            raise ValueError('Given object is no Compiler deriving class')
        self._registry[self.name] = compiler
        return compiler

    @classmethod
    def get(cls, name):
        """Return compiler instance by name.

        :param name: Name of compiler.
        :return object: ``webresource.compiler.Compiler`` instance.
        """
        try:
            inst = cls._instances.get(name)
            return inst if inst \
                else cls._instances.setdefault(name, cls._registry[name]())
        except KeyError:
            msg = 'No compiler registered by name {}'.format(name)
            raise CompilerError(msg)

    @classmethod
    def all(cls):
        """Return all instanciared compilers.

        :return list: List of compiler instances.
        """
        return cls._instances.values()


class CompilerError(Exception):
    """Compiler related exception.
    """


class compiler_context(object):
    """Compiler context for a single compiler run.
    """
    data = threading.local()

    def __enter__(self):
        """Enter compiler context.

        Creates file descriptors mapping for this compiler run.

        :return object: self
        """
        self.data.fds = dict()
        return self

    def __exit__(self, type, value, traceback):
        """Exit compiler context.

        Closes all open file descriptors and deletes file descritor mapping.
        """
        for fd in self.data.fds.values():
            fd.close()
        del self.data.fds

    @classmethod
    def fd(cls, path):
        """Get filedescritor by path.

        :param path: Path of requested file descriptor.
        :return object: File descriptor object related to path.
        :raise CompilerError: If function gets called outside compiler run.
        """
        try:
            fd = cls.data.fds.get(path)
            if not fd:
                fd = cls.data.fds.setdefault(path, open(path, 'w'))
            return fd
        except AttributeError:
            msg = 'Invalid call to ``fd`` outside compiler run'
            raise CompilerError(msg)

    @classmethod
    def paths(cls):
        """Get paths of all open file descriptors.

        :return list: List of paths of open file descriptors.
        :raise CompilerError: If function gets called outside compiler run.
        """
        try:
            return cls.data.fds.keys()
        except AttributeError:
            msg = 'Invalid call to ``paths`` outside compiler run'
            raise CompilerError(msg)


@add_metaclass(abc.ABCMeta)
class Compiler(object):
    """Abstract compiler object.

    Each concrete compiler gets instanciated once.
    """

    compile_required = False
    """Flag whether compilation is required even in development mode.
    XXX: probably not needed at all
    """

    @abc.abstractmethod
    def compile_resource(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        """
        raise NotImplemented()

    @classmethod
    def post_compile(cls):
        """Function which gets called once per compilation run after all
        resources have been processed.
        """
        pass


@compiler('default')
class DefaultCompiler(Compiler):
    """Default compiler.
    """

    def compile_resource(self, res):
        """If target differs from source, contents of source file is written
        to target, otherwise compiler does nothing.

        :param res: ``webresource.resource.Resource`` instance.
        """
        if res.source_path == res.target_path:
            return
        with open(res.source_path, 'r') as src:
            tgt = compiler_context.fd(res.target_path)
            tgt.write(src.read())


try:
    import slimit
    SLIMIT_INSTALLED = True
except ImportError:
    SLIMIT_INSTALLED = False


@compiler('slimit')
class SlimitCompiler(Compiler):
    """Compiler utilizing ``slimit``.
    """

    mangle = False
    """Compile option whether to mangle in compiled output.
    """

    mangle_toplevel = False
    """Compile option whether to mangle toplevel in compiled output.
    """

    def __init__(self):
        """Initialize ``slimit`` compiler.
        """
        if not SLIMIT_INSTALLED:
            raise CompilerError('``slimit`` not installed')

    def compile_resource(self, res):
        """Compile resource using ``slimit``.

        :param res: ``webresource.resource.Resource`` instance.
        """
        if not isinstance(res, JSResource):
            raise ValueError('{} is no ``JSResource`` instance'.format(res))
        if res.source_path == res.target_path:
            msg = 'Compilation target must differ from source to avoid override'
            raise CompilerError(msg)
        mangle = self.mangle
        mangle_toplevel = self.mangle_toplevel
        opts = res.compiler_opts
        if opts:
            mangle = opts.get('mangle', mangle)
            mangle_toplevel = opts.get('mangle_toplevel', mangle_toplevel)
        with open(res.source_path, 'r') as f:
            src = slimit.minify(
                f.read(),
                mangle=mangle,
                mangle_toplevel=mangle_toplevel
            )
            tgt = compiler_context.fd(res.target_path)
            tgt.write(src)


try:
    import lesscpy
    LESSCPY_INSTALLED = True
except ImportError:
    LESSCPY_INSTALLED = False


@compiler('lesscpy')
class LesscpyCompiler(Compiler):
    """Compiler utilizing ``lesscpy``.
    """

    compile_required = True
    """Compilation is always required for LESS resource.
    """

    minify = True
    """Compile option whether to minify compiled output.
    """

    def __init__(self):
        """Initialize ``lesscpy`` compiler.
        """
        if not LESSCPY_INSTALLED:
            CompilerError('``lesscpy`` not installed')

    def compile_resource(self, res):
        """Compile resource using ``lesscpy``.

        :param res: ``webresource.resource.Resource`` instance.
        """
        if not isinstance(res, CSSResource):
            raise ValueError('{} is no ``CSSResource`` instance'.format(res))
        if res.source_path == res.target_path:
            msg = 'Compilation target must differ from source to avoid override'
            raise CompilerError(msg)
        minify = self.minify
        opts = res.compiler_opts
        if opts:
            minify = opts.get('minify', minify)
        with open(res.source_path, 'r') as f:
            src = lesscpy.compile(f, minify=minify)
            tgt = compiler_context.fd(res.target_path)
            tgt.write(src)


@compiler('webpack')
class WebpackCompiler(Compiler):
    """Compiler utilizing webpack.
    """
    static_target = 'webpack.config.js'

    def compile_resource(self, res):
        """Compile resource to get interpreted by ``webpack``.

        :param res: ``webresource.resource.Resource`` instance.
        """
        # XXX

    @classmethod
    def post_compile(cls):
        """Call webpack to process generated webpack config file.
        """
        # XXX


def _compile_resources(resources, timestamp, development=False, purge=False):
    """Compile resources.

    XXX: check compilation target against dependencies
    XXX: non compiled resources also must be added to target

    :param resources: List of resources to compile in correct dependency order.
    :param timestamp: modification timestamp.
    :param development: Flag whether development mode.
    :param purge: Flag whether to purge already compiled resource.
    """
    # iterate resources
    for res in resources:
        # source path must differ from target path if dedicated compiler defined
        source_path = res.source_path
        target_path = res.target_path
        if res.compiler and source_path == target_path:
            msg = 'No dedicated compilation target defined: {}'.format(res.uid)
            raise CompilerError(msg)
        # actual compiler to use
        compiler = res.compiler if res.compiler else 'default'
        # get compiler instance from registry
        cpl = compiler.get(compiler)
        # skip if development mode and no resource compilation required
        if development and not cpl.compile_required:
            continue
        # skip if source modification time matches target modification
        # time, target not points to bundle and no purge requested
        if os.path.getmtime(source_path) == os.path.getmtime(target_path) \
                and not res.target.startswith('uid:') and not purge:
            continue
        # lookup or create target file descriptor
        fd = fds.setdefault(target_path, open('w', target_path))
        fd.write('\n\n')
        fd.write(cpl.compile_resource(res))
        # set modification time of source file. this is necessary to detect
        # recompilation of bundles if one resource changed.
        os.utime(source_path, (timestamp, timestamp))


def compile_resources(development=False, purge=False):
    """Compile resources according to registered resource definitions.

    :param development: Flag whether development mode.
    :param purge: Flag whether to purge already compiled resource.
    """
    with compiler_context() as cc:
        # timestamp for setting modification time
        timestamp = time.time()
        # compile CSS resources
        _compile_resources(
            rr.resolve_css,
            timestamp,
            development=development,
            purge=purge
        )
        # compile JS resources
        _compile_resources(
            rr.resolve_js,
            timestamp,
            development=development,
            purge=purge
        )
        # call ``post_compile`` on all instanciated compilers.
        for cpl in compiler.all():
            cpl.post_compile()
        # write modification time for all touched target files.
        for path in cc.paths():
            os.utime(path, (timestamp, timestamp))
