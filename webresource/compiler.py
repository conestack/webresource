from webresource.compat import add_metaclass
from webresource.resource import resource_registry as rr
import abc
import os


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
    def get(cls, name):
        """Return compiler by name.

        :return class: ``webresource.compiler.Compiler`` class.
        """
        return cls._registry.get(name)


class CompilerError(Exception):
    """Compiler related exception.
    """


@add_metaclass(abc.ABCMeta)
class Compiler(object):
    """Abstract compiler object.
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
        mangle = True
        mangle_toplevel = True
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
        minify = True
        opts = res.compile_opts
        if opts:
            minify = opts.get('minify', minify)
        with open(res.source_path, 'r') as source:
            return lesscpy.compile(source, minify=minify)
