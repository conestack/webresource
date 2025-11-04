class ResourceError(ValueError):
    """Resource related exception."""


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
