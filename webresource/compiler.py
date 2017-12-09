from webresource.compat import add_metaclass
from webresource.resource import CSSResource
from webresource.resource import JSResource
from webresource.resource import resource_registry as rr
import abc
import os
import time


class compiler(object):
    """Compiler decorator and registry.
    """

    _registry = dict()
    """Registry for available compilers.
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
    def get(cls, name, **kw):
        """Return compiler by name.

        :param name: Name of compiler.
        :param *kw: Keyword arguments to pass to compiler constructor.
        :return object: ``webresource.compiler.Compiler`` instance.
        """
        try:
            return cls._registry[name](**kw)
        except KeyError:
            msg = 'No compiler registered by name {}'.format(name)
            raise CompilerError(msg)


class CompilerError(Exception):
    """Compiler related exception.
    """


@add_metaclass(abc.ABCMeta)
class Compiler(object):
    """Abstract compiler object.
    """

    compile_required = False
    """Flag whether compilation is required even in development mode.
    """

    @abc.abstractmethod
    def compile(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        :return string: Compiled outcome as atring.
        """
        raise NotImplemented()


@compiler('slimit')
class SlimitCompiler(Compiler):
    """Compiler utilizing ``slimit``.
    """

    mangle = True
    """Compile option whether to mangle in compiled output.
    """

    mangle_toplevel = True
    """Compile option whether to mangle toplevel in compiled output.
    """

    def __init__(self):
        """Initialize ``slimit`` compiler.
        """
        try:
            import slimit
        except ImportError:
            raise CompilerError('``slimit`` not installed')

    def compile(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        :return string: Compiled outcome as atring.
        """
        if not isinstance(res, JSResource):
            raise ValueError('{} is no ``JSResource`` instance'.format(res))
        mangle = self.mangle
        mangle_toplevel = self.mangle_toplevel
        opts = res.compile_opts
        if opts:
            mangle = opts.get('mangle', mangle)
            mangle_toplevel = opts.get('mangle_toplevel', mangle_toplevel)
        with open(res.source_path, 'r') as f:
            source = f.read()
        return slimit.minify(
            source,
            mangle=mangle,
            mangle_toplevel=mangle_toplevel
        )


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
        try:
            import lesscpy
        except ImportError:
            raise CompilerError('``lesscpy`` not installed')

    def compile(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        :return string: Compiled outcome as atring.
        """
        if not isinstance(res, CSSResource):
            raise ValueError('{} is no ``CSSResource`` instance'.format(res))
        minify = self.minify
        opts = res.compile_opts
        if opts:
            minify = opts.get('minify', minify)
        with open(res.source_path, 'r') as source:
            return lesscpy.compile(source, minify=minify)


def _compile_resources(resources, development=False, purge=False):
    """Compile resources.

    :param resources: List of resources to compile in correct dependency order.
    :param development: Flag whether development mode.
    :param purge: Flag whether to purge already compiled resource.
    """
    # container for file descriptors
    fds = dict()
    # timestamp for setting modification time
    now = time.time()
    # iterate resources
    for res in resources:
        # skip if no compiler defined
        if not res.compiler:
            continue
        # source path must differ from target path if compiler defined
        source_path = res.source_path
        target_path = res.target_path
        if source_path == target_path:
            msg = 'No dedicated compilation target defined: {}'.format(res.uid)
            raise CompilerError(msg)
        # get compiler instance from registry
        cpl = compiler.get(res.compiler)
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
        fd.write(cpl.compile(res))
        # set modification time of source file for detecting recompilation
        os.utime(source_path, (now, now))
    # close open file descriptors
    for fd in fds.values():
        fd.close()
    # write modification time for all touched target files.
    for path in fds.keys():
        os.utime(path, (now, now))


def compile(development=False, purge=False):
    """Compile resources according to registered resource definitions.

    :param development: Flag whether development mode.
    :param purge: Flag whether to purge already compiled resource.
    """
    _compile_resources(rr.resolve_css, development=development, purge=purge)
    _compile_resources(rr.resolve_js, development=development, purge=purge)
