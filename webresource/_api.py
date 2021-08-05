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

    def __init__(self):
        self.development = False


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
                 resource=None, compressed=None, include=True, group=None,
                 crossorigin=None, referrerpolicy=None, type_=None):
        """Create resource.

        :param name: The resource unique name.
        :param depends: Optional name of dependency resource.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        :param group: Optional resource group instance.
        :param crossorigin: Sets the mode of the request to an HTTP CORS Request.
        :param referrerpolicy: Specifies which referrer information to send when
        fetching the resource.
        :param type_: Specifies the media type of the resource.
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
        self.crossorigin = crossorigin
        self.referrerpolicy = referrerpolicy
        self.type_ = type_

    @property
    def file_name(self):
        """Resource file name depending on operation mode.
        """
        if not config.development and self.compressed:
            return self.compressed
        return self.resource

    @property
    def file_path(self):
        """Absolute resource file path depending on operation mode.
        """
        return os.path.join(self.directory, self.file_name)

    def resource_url(self, base_url):
        path = self.path.strip('/')
        if path:
            parts = [base_url.strip('/'), path, self.file_name]
        else:
            parts = [base_url.strip('/'), self.file_name]
        return u'/'.join(parts)

    def render(self, base_url):
        raise NotImplementedError('Abstract resource not implements ``render``')

    def _render_tag(self, tag, closing_tag, **attrs):
        attrs_ = list()
        for name, val in attrs.items():
            if val is None:
                continue
            attrs_.append(u'{0}="{1}"'.format(name, val))
        attrs_ = u' {0}'.format(u' '.join(sorted(attrs_)))
        if not closing_tag:
            return u'<{tag}{attrs} />'.format(tag=tag, attrs=attrs_)
        return u'<{tag}{attrs}></{tag}>'.format(tag=tag, attrs=attrs_)

    def __repr__(self):
        return (
            '<{} name="{}", depends="{}", path="{}">'
        ).format(
            self.__class__.__name__,
            self.name,
            self.depends,
            self.path
        )


class ScriptResource(Resource):
    """A Javascript resource.
    """

    def __init__(self, name, depends='', directory=None, path='/',
                 resource=None, compressed=None, include=True, group=None,
                 crossorigin=None, referrerpolicy=None, type_=None, async_=None,
                 defer=None, integrity=None, nomodule=None):
        """Create script resource.

        :param name: The resource unique name.
        :param depends: Optional name of dependency resource.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        :param group: Optional resource group instance.
        :param crossorigin: Sets the mode of the request to an HTTP CORS Request.
        :param referrerpolicy: Specifies which referrer information to send when
        fetching the resource.
        :param type_: Specifies the media type of the resource.
        :param async_: Specifies that the script is executed asynchronously
        (only for external scripts)
        :param defer: Specifies that the script is executed when the page has
        finished parsing (only for external scripts).
        :param integrity: Allows a browser to check the fetched script to ensure
        that the code is never loaded if the source has been manipulated.
        :param nomodule: Allows a browser to check the fetched script to ensure
        that the code is never loaded if the source has been manipulated.
        """
        super(ScriptResource, self).__init__(
            name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            group=group, crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_=type_
        )
        self.async_ = async_
        self.defer = defer
        self.integrity = integrity
        self.nomodule = nomodule

    def render(self, base_url):
        return self._render_tag('script', True, **{
            'src': self.resource_url(base_url),
            'crossorigin': self.crossorigin,
            'referrerpolicy': self.referrerpolicy,
            'type': self.type_,
            'async': self.async_,
            'defer': self.defer,
            'integrity': self.integrity,
            'nomodule': self.nomodule
        })


class LinkResource(Resource):
    """A Link Resource.
    """

    def __init__(self, name, depends='', directory=None, path='/',
                 resource=None, compressed=None, include=True, group=None,
                 crossorigin=None, referrerpolicy=None, type_=None,
                 hreflang=None, media=None, rel=None, sizes=None, title=None):
        """Create link resource.

        :param name: The resource unique name.
        :param depends: Optional name of dependency resource.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        :param group: Optional resource group instance.
        :param crossorigin: Sets the mode of the request to an HTTP CORS Request.
        :param referrerpolicy: Specifies which referrer information to send when
        fetching the resource.
        :param type_: Specifies the media type of the resource.
        :param hreflang: Specifies the language of the text in the linked
        document.
        :param media: Specifies on what device the linked document will be
        displayed.
        :param rel: Required. Specifies the relationship between the current
        document and the linked document.
        :param sizes: Specifies the size of the linked resource. Only for
        rel="icon".
        :param title: Defines a preferred or an alternate stylesheet.
        """
        super(LinkResource, self).__init__(
            name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            group=group, crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_=type_
        )
        self.hreflang = hreflang
        self.media = media
        self.rel = rel
        self.sizes = sizes
        self.title = title

    def render(self, base_url):
        return self._render_tag('link', False, **{
            'href': self.resource_url(base_url),
            'crossorigin': self.crossorigin,
            'referrerpolicy': self.referrerpolicy,
            'type': self.type_,
            'hreflang': self.hreflang,
            'media': self.media,
            'rel': self.rel,
            'sizes': self.sizes,
            'title': self.title
        })


class StyleResource(LinkResource):
    """A Stylesheet Resource.
    """

    def __init__(self, name, depends='', directory=None, path='/',
                 resource=None, compressed=None, include=True, group=None,
                 crossorigin=None, referrerpolicy=None, hreflang=None,
                 media='all', rel='stylesheet', sizes=None,
                 title=None):
        """Create link resource.

        :param name: The resource unique name.
        :param depends: Optional name of dependency resource.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
        include the resource.
        :param group: Optional resource group instance.
        :param crossorigin: Sets the mode of the request to an HTTP CORS Request.
        :param referrerpolicy: Specifies which referrer information to send when
        fetching the resource.
        :param hreflang: Specifies the language of the text in the linked
        document.
        :param media: Specifies on what device the linked document will be
        displayed. Defaults to "all".
        :param rel: Specifies the relationship between the current document and
        the linked document. Defaults to "stylesheet".
        :param title: Defines a preferred or an alternate stylesheet.
        """
        super(StyleResource, self).__init__(
            name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            group=group, crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_='text/css', hreflang=hreflang, media=media, rel=rel,
            sizes=None, title=title
        )


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

    def __init__(self, resolver, base_url='https://tld.org'):
        """Create resource renderer.

        :param resolver: ``ResourceResolver`` instance.
        :param base_url: Base URL to render resource HTML tags.
        """
        self.resolver = resolver
        self.base_url = base_url

    def render(self):
        return u'\n'.join([
            res.render(self.base_url) for res in self.resolver.resolve()
        ])
