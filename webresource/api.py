from collections import Counter
import hashlib
import inspect
import logging
import os
import tempfile


logger = logging.getLogger('webresource')


class ResourceConfig(object):
    """Config singleton for web resources.
    """

    def __init__(self, _merge_dir=None):
        self.debug = False
        self._merge_dir = _merge_dir

    @property
    def merge_dir(self):
        if not self._merge_dir:
            self._merge_dir = tempfile.mkdtemp()
        return self._merge_dir

    @merge_dir.setter
    def merge_dir(self, path):
        self._merge_dir = path


config = ResourceConfig()


class ResourceMixin(object):
    """Mixin for ``Resource`` and ``ResourceGroup``.
    """

    def __init__(self, include):
        self._include = include

    @property
    def include(self):
        if callable(self._include):
            return self._include()
        return self._include


class Resource(ResourceMixin):
    """A web resource.
    """

    def __init__(self, name, depends='', directory=None, path='/',
                 resource=None, compressed=None, mergeable=False,
                 include=True, group=None, _config=config):
        """Create resource.

        :param name: The resource unique name.
        :param depends: Optional name of dependency resource.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param mergeable: Flag whether it's safe to merge resource with other
        resources.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        :param group: Optional resource group instance.
        """
        super(Resource, self).__init__(include)
        self.name = name
        self.depends = depends
        if not directory:
            module = inspect.getmodule(inspect.currentframe().f_back)
            directory = os.path.dirname(os.path.abspath(module.__file__))
        self.directory = directory
        self.path = path
        if resource is None:
            raise ValueError('No resource given')
        self.resource = resource
        self.compressed = compressed
        if group:
            group.add(self)
        self.mergeable = mergeable
        self._config = _config

    @property
    def file_name(self):
        """Resource file name depending on operation mode.
        """
        if not self._config.debug and self.compressed:
            return self.compressed
        return self.resource

    @property
    def file_path(self):
        """Absolute resource file path depending on operation mode.
        """
        return os.path.join(self.directory, self.file_name)

    def __repr__(self):
        return (
            '<{} name="{}", depends="{}", path="{}" mergeable={}>'
        ).format(
            self.__class__.__name__,
            self.name,
            self.depends,
            self.path,
            self.mergeable
        )


class JSResource(Resource):
    """A Javascript resource.
    """
    _type = 'js'


class CSSResource(Resource):
    """A CSS Resource.
    """
    _type = 'css'


class ResourceGroup(ResourceMixin):
    """A resource group.
    """

    def __init__(self, name, include=True):
        """Create resource group.

        :param name: The resource group name.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        """
        super(ResourceGroup, self).__init__(include)
        self.name = name
        self._members = []

    @property
    def members(self):
        return self._members

    def add(self, member):
        """Add member to resource group.

        :param member: Either ``ResourceGroup`` or ``Resource`` instance.
        """
        if not isinstance(member, (ResourceGroup, Resource)):
            raise ValueError(
                'Resource group can only contain instances '
                'of ``ResourceGroup`` or ``Resource``'
            )
        self._members.append(member)

    def __repr__(self):
        return '<{} name="{}">'.format(
            self.__class__.__name__,
            self.name
        )


class ResourceConflictError(ValueError):

    def __init__(self, counter):
        conflicting = list()
        for name, count in counter.items():
            if count > 1:
                conflicting.append(name)
        msg = 'Conflicting resource names: {}'.format(conflicting)
        super(ResourceConflictError, self).__init__(msg)


class ResourceCircularDependencyError(ValueError):

    def __init__(self, resources):
        msg = 'Resources define circular dependencies: {}'.format(resources)
        super(ResourceCircularDependencyError, self).__init__(msg)


class ResourceMissingDependencyError(ValueError):

    def __init__(self, resources):
        msg = 'Resource define missing dependency: {}'.format(resources)
        super(ResourceMissingDependencyError, self).__init__(msg)


class ResourceResolver(object):
    """Resource resolver.
    """

    def __init__(self, members):
        """Create resource resolver.

        :param members: Either single or list of ``Resource`` or
        ``ResourceGroup`` instances.
        """
        if not isinstance(members, (list, tuple)):
            members = [members]
        for member in members:
            if not isinstance(member, (Resource, ResourceGroup)):
                raise ValueError(
                    'members can only contain instances '
                    'of ``ResourceGroup`` or ``Resource``'
                )
        self.members = members

    def _flat_resources(self, members=None):
        if members is None:
            members = self.members
        resources = []
        for member in members:
            if not member.include:
                continue
            if isinstance(member, ResourceGroup):
                resources += self._flat_resources(members=member.members)
            else:
                resources.append(member)
        return resources

    def resolve(self):
        resources = self._flat_resources()
        names = [res.name for res in resources]
        counter = Counter(names)
        if len(resources) != len(counter):
            raise ResourceConflictError(counter)
        ret = []
        handled = {}
        for resource in resources[:]:
            if not resource.depends:
                ret.append(resource)
                handled[resource.name] = resource
                resources.remove(resource)
            elif not resource.depends in names:
                raise ResourceMissingDependencyError(resource)
        count = len(resources)
        while count > 0:
            count -= 1
            for resource in resources[:]:
                if resource.depends in handled:
                    dependency = handled[resource.depends]
                    index = ret.index(dependency)
                    ret.insert(index + 1, resource)
                    handled[resource.name] = resource
                    resources.remove(resource)
                    break
        if resources:
            raise ResourceCircularDependencyError(resources)
        return ret


class ResourceRenderer(object):
    """Resource renderer.
    """

    def __init__(self, resolver, base_url='https://tld.org', _config=config):
        """Create resource renderer.

        :param resolver: ``ResourceResolver`` instance.
        :param base_url: Base URL to render resource HTML tags.
        """
        self.resolver = resolver
        self.base_url = base_url
        self._config = _config

    def _js_tag(self, path):
        return '<script src="{}{}"></script>\n'.format(self.base_url, path)

    def _css_tag(self, path, media='all'):
        return (
            '<link href="{}{}" rel="stylesheet" type="text/css" media="{}">\n'
        ).format(self.base_url, path, media)

    def _hashed_name(self, names, ext):
        hash_ = hashlib.sha256(''.join(names).encode('utf-8')).hexdigest()
        return '{}.{}'.format(hash_, ext)

    def render(self):
        pass
