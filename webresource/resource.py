from webresource.compat import add_metaclass
import abc
import inspect
import logging
import os


logger = logging.getLogger('webresource')


class RegistryError(Exception):
    """Resource registry related exception.
    """


class ResourceGroup(object):
    """A resource group.
    """

    def __init__(self, uid, skip=False):
        """Create resource group.

        :param uid: The resource group unique identifier.
        :param skip: Flag whether to exclude this resource group from
            processing.
        """
        self.uid = uid
        self.skip = skip


@add_metaclass(abc.ABCMeta)
class Resource(object):
    """A web resource.
    """

    def __init__(self, uid, depends=None, resource_dir=None, source=None,
                 target=None, compiler=None, compiler_opts=None, prefix='/',
                 group=None):
        """Create resource instance.

        :param uid: The resource unique identifier.
        :param depends: Optional uid or list of uids of dependency resource.
        :param resource_dir: Directory containing the resource files.
        :param source: Source file for this resource.
        :param target: Bundling target. Either file name or dependency resource
            if value starts with ``uid:``. If development mode, compilation
            required and dependency resource defined as target, the compiled
            resource gets placed in the resource directory.
        :param compiler: Compiler to use.
        :param compiler_opts: Dict containing compiler options.
        :param prefix: Prefix for html tag link creation.
        :param group: Resource group uid if this resource belongs to a resource
            group.
        """
        self.uid = uid
        if not depends:
            depends = []
        elif not isinstance(depends, list) and not isinstance(depends, tuple):
            depends = [depends]
        self.depends = depends
        self.resource_dir = resource_dir
        self.source = source
        self.target = target
        self.compiler = compiler
        self.compiler_opts = compiler_opts
        self.prefix = prefix
        self.group = group

    def __repr__(self):
        return (
            '<{} object, uid={}, depends={}, source={}, '
            'target={}, compiler={}, prefix={}>'
        ).format(
            self.__class__.__name__,
            self.uid,
            self.depends,
            self.source,
            self.target,
            self.compiler,
            self.prefix
        )

    @abc.abstractproperty
    def registry(self):
        """Registry dict related to this resource.
        """
        raise NotImplemened()

    @property
    def source_path(self):
        """Absolute path to resource source.
        """
        return os.path.join(self.resource_dir, self.source)

    @property
    def target_path(self):
        """Absolute path to resource target.
        """
        target = self.target
        if not target:
            target = self.source
        if target.startswith('uid:'):
            res = self.registry.get(target[4:])
            if not res:
                msg = 'Dependency resource {} not exists'.format(target[4:])
                raise RegistryError(msg)
            return res.target_path
        return os.path.join(self.resource_dir, target)


class JSResource(Resource):
    """A Javascript resource.
    """

    @property
    def registry(self):
        """Javascript registry dict.
        """
        return resource_registry.js


class CSSResource(Resource):
    """A CSS Resource.
    """

    @property
    def registry(self):
        """CSS registry dict.
        """
        return resource_registry.css


class resource_registry(object):
    """Resource registry singleton.
    """

    groups = dict()
    """Resource groups dict.
    """

    js = dict()
    """Javascript resources registry dict.
    """

    css = dict()
    """CSS resources registry dict.
    """

    @staticmethod
    def _register(reg, res):
        """Register given resource in given registry.

        :param reg: Registry dict.
        :param res: Resouce instance.
        """
        if res.uid in reg:
            old_res = reg[res.uid]
            msg = 'Resource {} gets overwritten with {}'.format(old_res, res)
            logger.info(msg)
        reg[res.uid] = res

    # XXX: classmethod
    @staticmethod
    def _resolve(reg):
        """Resolve dependency tree of given registry and return resources in
        correct order.

        :param reg: Registry dict.
        :return list: Resources sorted by dependency from passed registry dict.
        """
        def skip(res):
            group = reg[res].group
            if group and resource_registry.groups[group].skip:
                return True
            return False
        res = [r for r in reg.keys() if not skip(r)]
        cnt = len(res)
        deps = dict()
        def sort():
            for i in range(cnt):
                for dep in reg[res[i]].depends:
                    try:
                        j = res.index(dep)
                    except ValueError:
                        msg = 'Dependency resource {} not exists'.format(dep)
                        raise RegistryError(msg)
                    deps.setdefault(res[i], set()).add(dep)
                    if res[i] in deps.setdefault(dep, set()):
                        msg = 'Circular dependency {} - {}'.format(dep, res[i])
                        raise RegistryError(msg)
                    if j > i:
                        res[i], res[j] = res[j], res[i]
                        sort()
        sort()
        # XXX: sort by target
        return [reg[k] for k in res]

    @classmethod
    def register_group(cls, group):
        """Register resource group.

        :param group: ResourceGroup instance.
        """
        groups = cls.groups
        if group.uid in groups:
            old_group = groups[group.uid]
            msg = 'ResourceGroup {} gets overwritten with {}'.format(
                old_group, group)
            logger.info(msg)
        groups[group.uid] = group

    @classmethod
    def register_js(cls, res):
        """Register Javascript resource.

        :param res: JSResource instance.
        """
        if not isinstance(res, JSResource):
            raise ValueError('{} is no ``JSResource`` instance'.format(res))
        cls._register(cls.js, res)

    @classmethod
    def resolve_js(cls):
        """Resolve dependency tree of Javascript resources and return them
        in correct order.

        :return list: Javascript resources sorted by dependency.
        """
        return cls._resolve(cls.js)

    @classmethod
    def register_css(cls, res):
        """Register CSS resource.

        :param res: CSSResource instance.
        """
        if not isinstance(res, CSSResource):
            raise ValueError('{} is no ``CSSResource`` instance'.format(res))
        cls._register(cls.css, res)

    @classmethod
    def resolve_css(cls):
        """Resolve dependency tree of CSS resources and return them
        in correct order.

        :return list: CSS resources sorted by dependency.
        """
        return cls._resolve(cls.css)


def resource_group(uid, skip=False):
    """Register a resource group.

    :param uid: Unique identifyer of resource group.
    :param skip: Flag whether to skip inclusion of resource group related
        resources.
    :return object: ResourceGroup instance.
    """
    group = ResourceGroup(uid, skip=skip)
    resource_registry.register_group(group)
    return group


def js_resource(uid, depends=None, resource_dir=None, source=None,
                target=None, compiler=None, compiler_opts=None, prefix='/'):
    """Register a Javascript resource.

    :param uid: The resource unique identifier.
    :param depends: Optional uid or list of uids of dependency resource.
    :param resource_dir: Directory containing the resource files. If not given,
        resource directory gets calculated from calling package.
    :param source: Source file for this resource.
    :param target: Bundling target. Either file name or dependency resource
        if value starts with ``uid:``. If development mode, compilation
        required and dependency resource defined as target, the compiled
        resource gets placed in the resource directory.
    :param compiler: Compiler to use.
    :param compiler_opts: Dict containing compiler options.
    :param prefix: Prefix for html tag link creation.
    :return object: JSResource instance.
    """
    if not resource_dir:
        module = inspect.getmodule(inspect.currentframe().f_back)
        resource_dir = os.path.dirname(os.path.abspath(module.__file__))
    res = JSResource(
        uid,
        depends=depends,
        source=source,
        resource_dir=resource_dir,
        target=target,
        compiler=compiler,
        compiler_opts=compiler_opts,
        prefix=prefix
    )
    resource_registry.register_js(res)
    return res


def css_resource(uid, depends=None, resource_dir=None, source=None,
                 target=None, compiler=None, compiler_opts=None, prefix='/'):
    """Register a CSS resource.

    :param uid: The resource unique identifier.
    :param depends: Optional uid or list of uids of dependency resource.
    :param resource_dir: Directory containing the resource files. If not given,
        resource directory gets calculated from calling package.
    :param source: Source file for this resource.
    :param target: Bundling target. Either file name or dependency resource
        if value starts with ``uid:``. If development mode, compilation
        required and dependency resource defined as target, the compiled
        resource gets placed in the resource directory.
    :param compiler: Compiler to use.
    :param compiler_opts: Dict containing compiler options.
    :param prefix: Prefix for html tag link creation.
    :return object: CSSResource instance.
    """
    if not resource_dir:
        module = inspect.getmodule(inspect.currentframe().f_back)
        resource_dir = os.path.dirname(os.path.abspath(module.__file__))
    res = CSSResource(
        uid,
        depends=depends,
        source=source,
        resource_dir=resource_dir,
        target=target,
        compiler=compiler,
        compiler_opts=compiler_opts,
        prefix=prefix
    )
    resource_registry.register_css(res)
    return res
