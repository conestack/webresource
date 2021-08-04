import inspect
import logging
import os
import tempfile


logger = logging.getLogger('webresource')


class Config(object):
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


config = Config()


class Resource(object):
    """A web resource.
    """

    def __init__(self, name, depends=None, directory=None, path='/',
                 resource=None, compressed=None, mergeable=False,
                 include=True, group=None, _config=config):
        """Create resource.

        :param name: The resource unique name.
        :param depends: Optional name or list of names of dependency resource.
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
        self.name = name
        if not depends:
            depends = []
        elif not isinstance(depends, (list, tuple)):
            depends = [depends]
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
        self.include = include
        self._config = _config

    @property
    def file_path(self):
        """Absolute resource file path depending on operation mode.
        """
        if not self._config.debug and self.compressed:
            file = self.compressed
        else:
            file = self.resource
        return os.path.join(self.directory, file)

    def __repr__(self):
        return (
            '<{} name="{}", depends=[{}], path="{}" mergeable={}>'
        ).format(
            self.__class__.__name__,
            self.name,
            ','.join(self.depends),
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


class ResourceGroup(object):
    """A resource group.
    """

    def __init__(self, name, include=True):
        """Create resource group.

        :param name: The resource group unique name.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        """
        self.name = name
        self.include = include
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
        return '<{} name="{}"">'.format(
            self.__class__.__name__,
            self.name
        )


class Resolver(object):
    """Resource resolver.
    """

    def __init__(self, members, _config=config):
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
        self._config = _config

    def _flat_resource(self, members=None):
        if members is None:
            members = self.members
        resources = list()
        for member in members:
            if callable(member.include):
                include = member.include()
            else:
                include = member.include
            if not include:
                continue
            if isinstance(member, ResourceGroup):
                resources += self._flat_resources(members=member.members)
            else:
                resources.append(member)
        return resources

    def _resolve(self):
        resources = self._flat_resources()
        names = [resource.name for resource in resources]
        def cmp(a, b):
            if a.depends is None:
                return 0
            if a.depends not in names:
                msg = 'Undefined dependencs "{}" defined in "{}"'.format(
                    a.depends,
                    a.name
                )
                raise ValueError(msg)
            if a.depends == b.depends:
                return 1
            return -1
        return sorted(resources, cmp=cmp)
