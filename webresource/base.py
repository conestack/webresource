from webresource.exceptions import ResourceError

import copy
import os


class ResourceMixin(object):
    """Mixin for ``Resource`` and ``ResourceGroup``."""

    def __init__(self, name='', directory=None, path=None, include=True, group=None):
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
