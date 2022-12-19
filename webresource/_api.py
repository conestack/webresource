from collections import Counter
import base64
import copy
import hashlib
import logging
import os
import sys
import uuid


try:
    FileNotFoundError
except NameError:  # pragma: nocover
    FileNotFoundError = EnvironmentError


logger = logging.getLogger(__name__)
is_py3 = sys.version_info[0] >= 3
namespace_uuid = uuid.UUID('f3341b2e-f97e-40d2-ad2f-10a08a778877')


class ResourceConfig(object):
    """Config singleton for web resources."""

    def __init__(self):
        self.development = False


config = ResourceConfig()


class ResourceError(ValueError):
    """Resource related exception."""


class ResourceMixin(object):
    """Mixin for ``Resource`` and ``ResourceGroup``."""

    def __init__(
        self, name='', directory=None, path=None, include=True, group=None
    ):
        self.name = name
        self.directory = directory
        self.path = path
        self.include = include
        self.parent = None
        if group:
            group.add(self)

    @property
    def path(self):
        if self._path is not None:
            return self._path
        if self.parent is not None:
            return self.parent.path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def directory(self):
        if self._directory is not None:
            return self._directory
        if self.parent is not None:
            return self.parent.directory

    @directory.setter
    def directory(self, directory):
        if directory is None:
            self._directory = None
            return
        self._directory = os.path.abspath(directory)

    @property
    def include(self):
        if callable(self._include):
            return self._include()
        return self._include

    @include.setter
    def include(self, include):
        self._include = include

    def remove(self):
        """Remove resource or resource group from parent group."""
        if not self.parent:
            raise ResourceError('Object is no member of a resource group')
        self.parent.members.remove(self)
        self.parent = None

    def copy(self):
        """Return a deep copy of this object."""
        return copy.deepcopy(self)


class Resource(ResourceMixin):
    """A web resource."""

    _hash_algorithms = dict(
        sha256=hashlib.sha256,
        sha384=hashlib.sha384,
        sha512=hashlib.sha512
    )

    def __init__(
        self, name='', depends=None, directory=None, path=None,
        resource=None, compressed=None, include=True, unique=False,
        unique_prefix='++webresource++', hash_algorithm='sha384', group=None,
        url=None, crossorigin=None, referrerpolicy=None, type_=None, **kwargs
    ):
        """Base class for resources.

        :param name: The resource unique name.
        :param depends: Optional name or list of names of dependency resources.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
            include the resource.
        :param unique: Flag whether to render resource URL including unique key.
            Has no effect if ``url`` is given.
        :param unique_prefix: Prefix for unique key. Defaults to
            '++webresource++'.
        :param hash_algorithm: Name of the hashing algorithm. Either 'sha256',
            'sha384' or 'sha512'. Defaults to 'sha384'.
        :param group: Optional resource group instance.
        :param url: Optional resource URL to use for external resources.
        :param crossorigin: Sets the mode of the request to an HTTP CORS Request.
        :param referrerpolicy: Specifies which referrer information to send when
            fetching the resource.
        :param type_: Specifies the media type of the resource.
        :param **kwargs: Additional keyword arguments. Gets rendered as
            additional attributes on resource tag.
        :raise ResourceError: No resource and no url given.
        """
        if resource is None and url is None:
            raise ResourceError('Either resource or url must be given')
        super(Resource, self).__init__(
            name=name, directory=directory, path=path,
            include=include, group=group
        )
        self.depends = (
            (depends if isinstance(depends, (list, tuple)) else [depends])
            if depends else None
        )
        self.resource = resource
        self.compressed = compressed
        self.unique = unique
        self.unique_prefix = unique_prefix
        self.hash_algorithm = hash_algorithm
        self.file_hash = None
        self.url = url
        self.crossorigin = crossorigin
        self.referrerpolicy = referrerpolicy
        self.type_ = type_
        self.additional_attrs = kwargs

    @property
    def file_name(self):
        """Resource file name depending on operation mode."""
        if not config.development and self.compressed:
            return self.compressed
        return self.resource

    @property
    def file_path(self):
        """Absolute resource file path depending on operation mode."""
        directory = self.directory
        if not directory:
            raise ResourceError('No directory set on resource.')
        return os.path.join(directory, self.file_name)

    @property
    def file_data(self):
        """File content of resource depending on operation mode."""
        with open(self.file_path, 'rb') as f:
            return f.read()

    @property
    def file_hash(self):
        """Hash of resource file content."""
        if not config.development and self._file_hash is not None:
            return self._file_hash
        hash_func = self._hash_algorithms[self.hash_algorithm]
        hash_ = base64.b64encode(hash_func(self.file_data).digest())
        hash_ = hash_.decode() if is_py3 else hash_
        self.file_hash = hash_
        return hash_

    @file_hash.setter
    def file_hash(self, hash_):
        self._file_hash = hash_

    @property
    def unique_key(self):
        return u'{}{}'.format(
            self.unique_prefix,
            str(uuid.uuid5(namespace_uuid, self.file_hash))
        )

    def resource_url(self, base_url):
        """Create URL for resource.

        :param base_url: The base URL to create the URL resource.
        """
        if self.url is not None:
            return self.url
        parts = [base_url.strip('/')]
        path = self.path
        if path:
            parts.append(path.strip('/'))
        if self.unique:
            parts.append(self.unique_key)
        parts.append(self.file_name)
        return u'/'.join(parts)

    def render(self, base_url):
        """Renders the resource HTML tag. must be implemented on subclass.

        :param base_url: The base URL to create the URL resource.
        :raise NotImplementedError: Method is abstract.
        """
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
            '<{} name="{}", depends="{}">'
        ).format(
            self.__class__.__name__,
            self.name,
            self.depends
        )


class ScriptResource(Resource):
    """A Javascript resource."""

    def __init__(
        self, name='', depends=None, directory=None, path=None,
        resource=None, compressed=None, include=True, unique=False,
        unique_prefix='++webresource++', hash_algorithm='sha384', group=None,
        url=None, crossorigin=None, referrerpolicy=None, type_=None,
        async_=None, defer=None, integrity=None, nomodule=None, **kwargs
    ):
        """Create script resource.

        :param name: The resource unique name.
        :param depends: Optional name or list of names of dependency resources.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
            include the resource.
        :param unique: Flag whether to render resource URL including unique key.
            Has no effect if ``url`` is given.
        :param unique_prefix: Prefix for unique key. Defaults to
            '++webresource++'.
        :param hash_algorithm: Name of the hashing algorithm. Either 'sha256',
            'sha384' or 'sha512'. Defaults to 'sha384'.
        :param group: Optional resource group instance.
        :param url: Optional resource URL to use for external resources.
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
            If integrity given and value is 'True', the integrity hash gets
            calculated from the resource file content. This automatic calculation
            won't work if ``url`` is given. If value is a string, it is assumed
            to be the already calculated resource hash and is taken as is.
        :param nomodule: Specifies that the script should not be executed in
            browsers supporting ES2015 modules.
        :param **kwargs: Additional keyword arguments. Gets rendered as
            additional attributes on resource tag.
        :raise ResourceError: No resource and no url given.
        """
        super(ScriptResource, self).__init__(
            name=name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            unique=unique, unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm, group=group, url=url,
            crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_=type_, **kwargs
        )
        self.async_ = async_
        self.defer = defer
        self.integrity = integrity
        self.nomodule = nomodule

    @property
    def integrity(self):
        if not self._integrity:
            return self._integrity
        if not config.development and self._integrity_hash is not None:
            return self._integrity_hash
        if self._integrity is True:
            self._integrity_hash = u'{}-{}'.format(
                self.hash_algorithm,
                self.file_hash
            )
        return self._integrity_hash

    @integrity.setter
    def integrity(self, integrity):
        if integrity is True:
            if self.url is not None:
                msg = 'Cannot calculate integrity hash from external resource'
                raise ResourceError(msg)
            self._integrity_hash = None
        else:
            self._integrity_hash = integrity
        self._integrity = integrity

    def render(self, base_url):
        """Renders the resource HTML ``script`` tag.

        :param base_url: The base URL to create the URL resource.
        """
        attrs = {
            'src': self.resource_url(base_url),
            'crossorigin': self.crossorigin,
            'referrerpolicy': self.referrerpolicy,
            'type': self.type_,
            'async': self.async_,
            'defer': self.defer,
            'integrity': self.integrity,
            'nomodule': self.nomodule
        }
        attrs.update(self.additional_attrs)
        return self._render_tag('script', True, **attrs)


class LinkMixin(Resource):
    """Mixin class for link resources."""

    def __init__(
        self, name='', depends=None, directory=None, path=None,
        resource=None, compressed=None, include=True, unique=False,
        unique_prefix='++webresource++', hash_algorithm='sha384', group=None,
        url=None, crossorigin=None, referrerpolicy=None, type_=None,
        hreflang=None, media=None, rel=None, sizes=None, title=None, **kwargs
    ):
        super(LinkMixin, self).__init__(
            name=name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            unique=unique, unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm, group=group, url=url,
            crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_=type_, **kwargs
        )
        self.hreflang = hreflang
        self.media = media
        self.rel = rel
        self.sizes = sizes
        self.title = title

    def render(self, base_url):
        """Renders the resource HTML ``link`` tag.

        :param base_url: The base URL to create the URL resource.
        """
        attrs = {
            'href': self.resource_url(base_url),
            'crossorigin': self.crossorigin,
            'referrerpolicy': self.referrerpolicy,
            'type': self.type_,
            'hreflang': self.hreflang,
            'media': self.media,
            'rel': self.rel,
            'sizes': self.sizes,
            'title': self.title
        }
        attrs.update(self.additional_attrs)
        return self._render_tag('link', False, **attrs)


class LinkResource(LinkMixin):
    """A Link Resource."""

    def __init__(
        self, name='', depends=None, directory=None, path=None,
        resource=None, compressed=None, include=True, unique=False,
        unique_prefix='++webresource++', hash_algorithm='sha384', group=None,
        url=None, crossorigin=None, referrerpolicy=None, type_=None,
        hreflang=None, media=None, rel=None, sizes=None, title=None, **kwargs
    ):
        """Create link resource.

        :param name: The resource unique name.
        :param depends: Optional name or list of names of dependency resources.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
            include the resource.
        :param unique: Flag whether to render resource URL including unique key.
            Has no effect if ``url`` is given.
        :param unique_prefix: Prefix for unique key. Defaults to
            '++webresource++'.
        :param hash_algorithm: Name of the hashing algorithm. Either 'sha256',
            'sha384' or 'sha512'. Defaults to 'sha384'.
        :param group: Optional resource group instance.
        :param url: Optional resource URL to use for external resources.
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
        :param **kwargs: Additional keyword arguments. Gets rendered as
            additional attributes on resource tag.
        :raise ResourceError: No resource and no url given.
        """
        super(LinkResource, self).__init__(
            name=name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            unique=unique, unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm, group=group, url=url,
            crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_=type_, hreflang=hreflang, media=media, rel=rel, sizes=sizes,
            title=title, **kwargs
        )


class StyleResource(LinkMixin):
    """A Stylesheet Resource."""

    def __init__(
        self, name='', depends=None, directory=None, path=None,
        resource=None, compressed=None, include=True, unique=False,
        unique_prefix='++webresource++', hash_algorithm='sha384', group=None,
        url=None, crossorigin=None, referrerpolicy=None, hreflang=None,
        media='all', rel='stylesheet', title=None, **kwargs
    ):
        """Create link resource.

        :param name: The resource unique name.
        :param depends: Optional name or list of names of dependency resources.
        :param directory: Directory containing the resource files.
        :param path: URL path for HTML tag link creation.
        :param resource: Resource file.
        :param compressed: Optional compressed version of resource file.
        :param include: Flag or callback function returning a flag whether to
            include the resource.
        :param unique: Flag whether to render resource URL including unique key.
            Has no effect if ``url`` is given.
        :param unique_prefix: Prefix for unique key. Defaults to
            '++webresource++'.
        :param hash_algorithm: Name of the hashing algorithm. Either 'sha256',
            'sha384' or 'sha512'. Defaults to 'sha384'.
        :param group: Optional resource group instance.
        :param url: Optional resource URL to use for external resources.
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
        :param **kwargs: Additional keyword arguments. Gets rendered as
            additional attributes on resource tag.
        :raise ResourceError: No resource and no url given.
        """
        super(StyleResource, self).__init__(
            name=name, depends=depends, directory=directory, path=path,
            resource=resource, compressed=compressed, include=include,
            unique=unique, unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm, group=group, url=url,
            crossorigin=crossorigin, referrerpolicy=referrerpolicy,
            type_='text/css', hreflang=hreflang, media=media, rel=rel,
            sizes=None, title=title, **kwargs
        )


class ResourceGroup(ResourceMixin):
    """A resource group."""

    def __init__(
        self, name='', directory=None, path=None, include=True, group=None
    ):
        """Create resource group.

        :param name: The resource group name.
        :param directory: Directory containing the resource files.
        :param path: Optional URL path for HTML tag link creation. Takes
            precedence over group members paths.
        :param include: Flag or callback function returning a flag whether to
            include the resource group.
        :param group: Optional resource group instance.
        """
        super(ResourceGroup, self).__init__(
            name=name, directory=directory, path=path,
            include=include, group=group
        )
        self._members = []

    @property
    def members(self):
        """List of group members.

        Group members are either instances of ``Resource`` or ``ResourceGroup``.
        """
        return self._members

    @property
    def scripts(self):
        """List of all contained ``ScriptResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(ScriptResource)

    @property
    def styles(self):
        """List of all contained ``StyleResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(StyleResource)

    @property
    def links(self):
        """List of all contained ``LinkResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(LinkResource)

    def add(self, member):
        """Add member to resource group.

        :param member: Either ``ResourceGroup`` or ``Resource`` instance.
        :raise ResourceError: Invalid member given.
        """
        if not isinstance(member, (ResourceGroup, Resource)):
            raise ResourceError(
                'Resource group can only contain instances '
                'of ``ResourceGroup`` or ``Resource``'
            )
        member.parent = self
        self._members.append(member)

    def _filtered_resources(self, type_, members=None):
        if members is None:
            members = self.members
        resources = []
        for member in members:
            if isinstance(member, ResourceGroup):
                resources += self._filtered_resources(
                    type_,
                    members=member.members
                )
            elif isinstance(member, type_):
                resources.append(member)
        return resources

    def __repr__(self):
        return '<{} name="{}">'.format(
            self.__class__.__name__,
            self.name
        )


class ResourceConflictError(ResourceError):
    """Multiple resources declared with the same name."""

    def __init__(self, counter):
        conflicting = list()
        for name, count in counter.items():
            if count > 1:
                conflicting.append(name)
        msg = 'Conflicting resource names: {}'.format(sorted(conflicting))
        super(ResourceConflictError, self).__init__(msg)


class ResourceCircularDependencyError(ResourceError):
    """Resources define circular dependencies."""

    def __init__(self, resources):
        msg = 'Resources define circular dependencies: {}'.format(resources)
        super(ResourceCircularDependencyError, self).__init__(msg)


class ResourceMissingDependencyError(ResourceError):
    """Resource depends on a missing resource."""

    def __init__(self, resource):
        msg = 'Resource defines missing dependency: {}'.format(resource)
        super(ResourceMissingDependencyError, self).__init__(msg)


class ResourceResolver(object):
    """Resource resolver."""

    def __init__(self, members):
        """Create resource resolver.

        :param members: Either single or list of ``Resource`` or
            ``ResourceGroup`` instances.
        :raise ResourceError: Members contain invalid member.
        """
        if not isinstance(members, (list, tuple)):
            members = [members]
        for member in members:
            if not isinstance(member, (Resource, ResourceGroup)):
                raise ResourceError(
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
        """Return all resources from members as flat list ordered by
        dependencies.

        :raise ResourceConflictError: Resource list contains conflicting names
        :raise ResourceMissingDependencyError: Dependency resource not included
        :raise ResourceCircularDependencyError: Circular dependency defined.
        """
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
            else:
                for dependency_name in resource.depends:
                    if dependency_name not in names:
                        raise ResourceMissingDependencyError(resource)
        count = len(resources)
        while count > 0:
            count -= 1
            for resource in resources[:]:
                hook_idx = 0
                not_yet = False
                for dependency_name in resource.depends:
                    if dependency_name in handled:
                        dependency = handled[dependency_name]
                        dep_idx = ret.index(dependency)
                        hook_idx = dep_idx if dep_idx > hook_idx else hook_idx
                    else:
                        not_yet = True
                        break
                if not_yet:
                    continue
                ret.insert(hook_idx + 1, resource)
                handled[resource.name] = resource
                resources.remove(resource)
                break
        if resources:
            raise ResourceCircularDependencyError(resources)
        return ret


class ResourceRenderer(object):
    """Resource renderer."""

    def __init__(self, resolver, base_url='https://tld.org'):
        """Create resource renderer.

        :param resolver: ``ResourceResolver`` instance.
        :param base_url: Base URL to render resource HTML tags.
        """
        self.resolver = resolver
        self.base_url = base_url

    def render(self):
        """Render resources."""
        return u'\n'.join([
            res.render(self.base_url) for res in self.resolver.resolve()
        ])


class GracefulResourceRenderer(ResourceRenderer):
    """Resource renderer, which does not fail but logs an exception."""

    def render(self):
        lines = []
        for resource in self.resolver.resolve():
            try:
                lines.append(resource.render(self.base_url))
            except (ResourceError, FileNotFoundError):
                msg = u'Failure to render resource "{}"'.format(resource.name)
                lines.append(u'<!-- {} - details in logs -->'.format(msg))
                logger.exception(msg)
        return u'\n'.join(lines)
