from __future__ import annotations

from collections import Counter
from webresource.exceptions import ResourceCircularDependencyError
from webresource.exceptions import ResourceConflictError
from webresource.exceptions import ResourceError
from webresource.exceptions import ResourceMissingDependencyError
from webresource.groups import ResourceGroup
from webresource.resources import Resource


class ResourceResolver:
    """Resource resolver."""

    members: list[Resource | ResourceGroup]

    def __init__(
        self, members: Resource | ResourceGroup | list[Resource | ResourceGroup]
    ) -> None:
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

    def _flat_resources(
        self, members: list[Resource | ResourceGroup] | None = None
    ) -> list[Resource]:
        if members is None:
            members = self.members
        resources: list[Resource] = []
        for member in members:
            if not member.include:
                continue
            if isinstance(member, ResourceGroup):
                resources += self._flat_resources(members=member.members)
            else:
                resources.append(member)
        return resources

    def resolve(self) -> list[Resource]:
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
                assert resource.depends is not None  # guaranteed by above loop
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
