from six import StringIO
from webresource.compat import add_metaclass
from webresource.resource import resource_registry
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
        """
        raise NotImplemented()


@compiler('slimit')
class SlimitCompiler(Compiler):
    """Compiler utilizing ``slimit``.
    """

    def __init__(self):
        """Initialize slimit compiler.
        """
        try:
            import slimit
        except ImportError:
            raise CompilerError('``slimit`` not installed')

    def compile(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        """
        source = 'var foo = \'foo\';'
        slimit.minify(source, mangle=True, mangle_toplevel=True)


@compiler('lesscpy')
class LesscpyCompiler(Compiler):
    """Compiler utilizing ``lesscpy``.
    """

    def __init__(self):
        """Initialize lesscpy compiler.
        """
        try:
            import lesscpy
        except ImportError:
            raise CompilerError('``lesscpy`` not installed')

    def compile(self, res):
        """Compile resource.

        :param res: ``webresource.resource.Resource`` instance.
        """
        source = 'a { border-width: 2px * 3; }'
        lesscpy.compile(StringIO(source), minify=True)
