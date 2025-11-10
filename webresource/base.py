from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from webresource.exceptions import ResourceError

import copy
import os


if TYPE_CHECKING:
    from webresource.groups import ResourceGroup


class ResourceMixin:
    """Mixin for ``Resource`` and ``ResourceGroup``."""

    name: str
    parent: ResourceGroup | None
    _path: str | None
    _directory: str | None
    _include: bool | Callable[[], bool]

    def __init__(
        self,
        name: str = '',
        directory: str | None = None,
        path: str | None = None,
        include: bool | Callable[[], bool] = True,
        group: ResourceGroup | None = None,
    ) -> None:
        self.name = name
        self.directory = directory
        self.path = path
        self.include = include
        self.parent = None
        if group:
            group.add(self)  # type: ignore[arg-type]

    @property
    def path(self) -> str | None:
        if self._path is not None:
            return self._path
        if self.parent is not None:
            return self.parent.path
        return None

    @path.setter
    def path(self, path: str | None) -> None:
        self._path = path

    @property
    def directory(self) -> str | None:
        if self._directory is not None:
            return self._directory
        if self.parent is not None:
            return self.parent.directory
        return None

    @directory.setter
    def directory(self, directory: str | None) -> None:
        if directory is None:
            self._directory = None
            return
        self._directory = os.path.abspath(directory)

    @property
    def include(self) -> bool:
        if callable(self._include):
            return self._include()
        return self._include

    @include.setter
    def include(self, include: bool | Callable[[], bool]) -> None:
        self._include = include

    def remove(self) -> None:
        """Remove resource or resource group from parent group."""
        if not self.parent:
            raise ResourceError('Object is no member of a resource group')
        self.parent.members.remove(self)  # type: ignore[arg-type]
        self.parent = None

    def copy(self) -> ResourceMixin:
        """Return a deep copy of this object."""
        return copy.deepcopy(self)
