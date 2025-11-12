from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
from webresource.base import ResourceMixin
from webresource.exceptions import ResourceError
from webresource.resources import LinkResource
from webresource.resources import Resource
from webresource.resources import ScriptResource
from webresource.resources import StyleResource


T = TypeVar('T', bound=Resource)


class ResourceGroup(ResourceMixin):
    """A resource group."""

    _members: list[Resource | ResourceGroup]

    def __init__(
        self,
        name: str = '',
        directory: str | None = None,
        path: str | None = None,
        include: bool | Callable[[], bool] = True,
        group: ResourceGroup | None = None,
    ) -> None:
        """Create resource group.

        :param name: The resource group name.
        :param directory: Directory containing the resource files.
        :param path: Optional URL path for HTML tag link creation. Takes
            precedence over group members paths.
        :param include: Flag or callback function returning a flag whether to
            include the resource group.
        :param group: Optional resource group instance.
        """
        super().__init__(
            name=name, directory=directory, path=path, include=include, group=group
        )
        self._members = []

    @property
    def members(self) -> list[Resource | ResourceGroup]:
        """List of group members.

        Group members are either instances of ``Resource`` or ``ResourceGroup``.
        """
        return self._members

    @property
    def scripts(self) -> list[ScriptResource]:
        """List of all contained ``ScriptResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(ScriptResource)

    @property
    def styles(self) -> list[StyleResource]:
        """List of all contained ``StyleResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(StyleResource)

    @property
    def links(self) -> list[LinkResource]:
        """List of all contained ``LinkResource`` instances.

        Resources from subsequent resource groups are included.
        """
        return self._filtered_resources(LinkResource)

    def add(self, member: Resource | ResourceGroup) -> None:
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

    def _filtered_resources(
        self, type_: type[T], members: list[Resource | ResourceGroup] | None = None
    ) -> list[T]:
        if members is None:
            members = self.members
        resources: list[T] = []
        for member in members:
            if isinstance(member, ResourceGroup):
                resources += self._filtered_resources(type_, members=member.members)
            elif isinstance(member, type_):
                resources.append(member)
        return resources

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} name="{self.name}"'
