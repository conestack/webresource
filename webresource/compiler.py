from webresource.compat import add_metaclass
import abc


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
        self._registry[self.name] = compiler
        return compiler

    @classmethod
    def get(cls, name):
        """Return compiler by name.

        :return class: ``webresource.compiler.Compiler`` class.
        """
        return cls._registry.get(name)


@add_metaclass(abc.ABCMeta)
class Compiler(object):
    """Abstract compiler object.
    """

    @abc.abstractmethod
    def compile(self, resource):
        """Compile resource.

        :param resource: ``webresource.resource.Resource`` instance.
        """
        raise NotImplemented()


@compiler('slimit')
class SlimitCompiler(Compiler):
    """Compiler utilizing ``slimit``.
    """


@compiler('lesscpy')
class LesscpyCompiler(Compiler):
    """Compiler utilizing ``lesscpy``.
    """
