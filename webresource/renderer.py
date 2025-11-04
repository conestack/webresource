from webresource.config import logger
from webresource.exceptions import ResourceError

try:
    FileNotFoundError
except NameError:  # pragma: nocover
    FileNotFoundError = EnvironmentError


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
