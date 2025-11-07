from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from webresource.resources import Resource


class ResourceError(ValueError):
    """Resource related exception."""


class ResourceConflictError(ResourceError):
    """Multiple resources declared with the same name."""

    def __init__(self, counter: Counter[str]) -> None:
        conflicting = list()
        for name, count in counter.items():
            if count > 1:
                conflicting.append(name)
        msg = f'Conflicting resource names: {sorted(conflicting)}'
        super().__init__(msg)


class ResourceCircularDependencyError(ResourceError):
    """Resources define circular dependencies."""

    def __init__(self, resources: list[Resource]) -> None:
        msg = f'Resources define circular dependencies: {resources}'
        super().__init__(msg)


class ResourceMissingDependencyError(ResourceError):
    """Resource depends on a missing resource."""

    def __init__(self, resource: Resource) -> None:
        msg = f'Resource defines missing dependency: {resource}'
        super().__init__(msg)
