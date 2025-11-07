from webresource.config import logger
from webresource.exceptions import ResourceError
from webresource.resolver import ResourceResolver


class ResourceRenderer:
    """Resource renderer."""

    resolver: ResourceResolver
    base_url: str

    def __init__(
        self, resolver: ResourceResolver, base_url: str = 'https://tld.org'
    ) -> None:
        """Create resource renderer.

        :param resolver: ``ResourceResolver`` instance.
        :param base_url: Base URL to render resource HTML tags.
        """
        self.resolver = resolver
        self.base_url = base_url

    def render(self) -> str:
        """Render resources."""
        return '\n'.join([res.render(self.base_url) for res in self.resolver.resolve()])


class GracefulResourceRenderer(ResourceRenderer):
    """Resource renderer, which does not fail but logs an exception."""

    def render(self) -> str:
        lines = []
        for resource in self.resolver.resolve():
            try:
                lines.append(resource.render(self.base_url))
            except (ResourceError, FileNotFoundError):
                msg = f'Failure to render resource "{resource.name}"'
                lines.append(f'<!-- {msg} - details in logs -->')
                logger.exception(msg)
        return '\n'.join(lines)
