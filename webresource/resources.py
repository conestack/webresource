from webresource.base import ResourceMixin
from webresource.config import config
from webresource.config import namespace_uuid
from webresource.exceptions import ResourceError

import base64
import hashlib
import os
import uuid


class Resource(ResourceMixin):
    """A web resource."""

    _hash_algorithms = dict(
        sha256=hashlib.sha256, sha384=hashlib.sha384, sha512=hashlib.sha512
    )

    def __init__(
        self,
        name='',
        depends=None,
        directory=None,
        path=None,
        resource=None,
        compressed=None,
        include=True,
        unique=False,
        unique_prefix='++webresource++',
        hash_algorithm='sha384',
        group=None,
        url=None,
        crossorigin=None,
        referrerpolicy=None,
        type_=None,
        **kwargs,
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
            name=name, directory=directory, path=path, include=include, group=group
        )
        self.depends = (
            (depends if isinstance(depends, (list, tuple)) else [depends])
            if depends
            else None
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
        hash_ = hash_.decode()
        self.file_hash = hash_
        return hash_

    @file_hash.setter
    def file_hash(self, hash_):
        self._file_hash = hash_

    @property
    def unique_key(self):
        return '{}{}'.format(
            self.unique_prefix, str(uuid.uuid5(namespace_uuid, self.file_hash))
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
        return '/'.join(parts)

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
            attrs_.append('{0}="{1}"'.format(name, val))
        attrs_ = ' {0}'.format(' '.join(sorted(attrs_)))
        if not closing_tag:
            return '<{tag}{attrs} />'.format(tag=tag, attrs=attrs_)
        return '<{tag}{attrs}></{tag}>'.format(tag=tag, attrs=attrs_)

    def __repr__(self):
        return ('{} name="{}", depends="{}"').format(
            self.__class__.__name__, self.name, self.depends
        )


class ScriptResource(Resource):
    """A Javascript resource."""

    def __init__(
        self,
        name='',
        depends=None,
        directory=None,
        path=None,
        resource=None,
        compressed=None,
        include=True,
        unique=False,
        unique_prefix='++webresource++',
        hash_algorithm='sha384',
        group=None,
        url=None,
        crossorigin=None,
        referrerpolicy=None,
        type_=None,
        async_=None,
        defer=None,
        integrity=None,
        nomodule=None,
        **kwargs,
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
            name=name,
            depends=depends,
            directory=directory,
            path=path,
            resource=resource,
            compressed=compressed,
            include=include,
            unique=unique,
            unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm,
            group=group,
            url=url,
            crossorigin=crossorigin,
            referrerpolicy=referrerpolicy,
            type_=type_,
            **kwargs,
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
            self._integrity_hash = '{}-{}'.format(self.hash_algorithm, self.file_hash)
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
            'nomodule': self.nomodule,
        }
        attrs.update(self.additional_attrs)
        return self._render_tag('script', True, **attrs)


class LinkMixin(Resource):
    """Mixin class for link resources."""

    def __init__(
        self,
        name='',
        depends=None,
        directory=None,
        path=None,
        resource=None,
        compressed=None,
        include=True,
        unique=False,
        unique_prefix='++webresource++',
        hash_algorithm='sha384',
        group=None,
        url=None,
        crossorigin=None,
        referrerpolicy=None,
        type_=None,
        hreflang=None,
        media=None,
        rel=None,
        sizes=None,
        title=None,
        **kwargs,
    ):
        super(LinkMixin, self).__init__(
            name=name,
            depends=depends,
            directory=directory,
            path=path,
            resource=resource,
            compressed=compressed,
            include=include,
            unique=unique,
            unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm,
            group=group,
            url=url,
            crossorigin=crossorigin,
            referrerpolicy=referrerpolicy,
            type_=type_,
            **kwargs,
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
            'title': self.title,
        }
        attrs.update(self.additional_attrs)
        return self._render_tag('link', False, **attrs)


class LinkResource(LinkMixin):
    """A Link Resource."""

    def __init__(
        self,
        name='',
        depends=None,
        directory=None,
        path=None,
        resource=None,
        compressed=None,
        include=True,
        unique=False,
        unique_prefix='++webresource++',
        hash_algorithm='sha384',
        group=None,
        url=None,
        crossorigin=None,
        referrerpolicy=None,
        type_=None,
        hreflang=None,
        media=None,
        rel=None,
        sizes=None,
        title=None,
        **kwargs,
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
            name=name,
            depends=depends,
            directory=directory,
            path=path,
            resource=resource,
            compressed=compressed,
            include=include,
            unique=unique,
            unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm,
            group=group,
            url=url,
            crossorigin=crossorigin,
            referrerpolicy=referrerpolicy,
            type_=type_,
            hreflang=hreflang,
            media=media,
            rel=rel,
            sizes=sizes,
            title=title,
            **kwargs,
        )


class StyleResource(LinkMixin):
    """A Stylesheet Resource."""

    def __init__(
        self,
        name='',
        depends=None,
        directory=None,
        path=None,
        resource=None,
        compressed=None,
        include=True,
        unique=False,
        unique_prefix='++webresource++',
        hash_algorithm='sha384',
        group=None,
        url=None,
        crossorigin=None,
        referrerpolicy=None,
        hreflang=None,
        media='all',
        rel='stylesheet',
        title=None,
        **kwargs,
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
            name=name,
            depends=depends,
            directory=directory,
            path=path,
            resource=resource,
            compressed=compressed,
            include=include,
            unique=unique,
            unique_prefix=unique_prefix,
            hash_algorithm=hash_algorithm,
            group=group,
            url=url,
            crossorigin=crossorigin,
            referrerpolicy=referrerpolicy,
            type_='text/css',
            hreflang=hreflang,
            media=media,
            rel=rel,
            sizes=None,
            title=title,
            **kwargs,
        )
