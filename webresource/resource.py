import logging


logger = logging.getLogger('webresource')


class RegistryError(Exception):
    """Resource registry related exception.
    """


class resource_registry(object):
    """Resource registry singleton.
    """
    _js = dict()
    _css = dict()

    @staticmethod
    def _register(reg, res):
        """Register given resource in given registry.

        :param reg: Registry dict.
        :param res: Resouce instance.
        """
        if res.uid in reg:
            old_res = reg[res.uid]
            msg = 'Resource {} gets overwritten with {}'.format(old_res, res)
            logger.info(msg)
        reg[res.uid] = res

    @staticmethod
    def _resolve(reg):
        """Resolve dependency tree of given registry and return resources in
        correct order.

        :param reg: Registry dict.
        """
        res = reg.keys()
        cnt = len(res)
        deps = dict()
        def sort():
            for i in range(cnt):
                for dep in reg[res[i]].depends:
                    try:
                        j = res.index(dep)
                    except ValueError:
                        msg = 'Dependency resource {} not exists'.format(dep)
                        raise RegistryError(msg)
                    deps.setdefault(res[i], set()).add(dep)
                    if res[i] in deps.setdefault(dep, set()):
                        msg = 'Circular dependency {} - {}'.format(dep, res[i])
                        raise RegistryError(msg)
                    if j > i:
                        res[i], res[j] = res[j], res[i]
                        sort()
        sort()
        return [reg[k] for k in res]

    @classmethod
    def register_js(cls, res):
        """Register Javascript resource.

        :param res: JSResource instance.
        """
        if not isinstance(res, JSResource):
            raise ValueError('{} is no ``JSResource`` instance'.format(res))
        cls._register(cls._js, res)

    @classmethod
    def resolve_js(cls):
        """Resolve dependency tree of Javascript resources and return them
        in correct order.
        """
        return cls._resolve(cls._js)

    @classmethod
    def register_css(cls, res):
        """Register CSS resource.

        :param res: CSSResource instance.
        """
        if not isinstance(res, CSSResource):
            raise ValueError('{} is no ``CSSResource`` instance'.format(res))
        cls._register(cls._css, res)        

    @classmethod
    def resolve_css(cls):
        """Resolve dependency tree of CSS resources and return them
        in correct order.
        """
        return cls._resolve(cls._css)


class Resource(object):
    """A web resource.
    """

    def __init__(self, uid, depends=None):
        """Create resource instance.

        :param uid: The resource unique identifier
        :param depends: Optional uid or list of uids of dependency resource
        """
        self.uid = uid
        if not depends:
            depends = []
        elif not isinstance(depends, list) and not isinstance(depends, tuple):
            depends = [depends]
        self.depends = depends

    def __repr__(self):
        return '<Resource object, uid={}, depends={}>'.format(
            self.uid,
            self.depends
        )


class JSResource(Resource):
    """A Javascript resource.
    """


class CSSResource(Resource):
    """A CSS Resource.
    """
