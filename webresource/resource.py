import logging


logger = logging.getLogger('webresource')


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
            ols_res = reg[res.uid]
            msg = 'Resource {} gets overwritten with {}'.format(old_res, res)
            logger.info(msg)
        reg[res.uid] = res

    @staticmethod
    def _resolve(reg):
        """Resolve dependency tree of given registry and return resources in
        correct order.

        :param reg: Registry dict.
        """
        deps = dict()
        for res in reg.values():
            depends = res.depends
            # no dependency, continue
            if not depends:
                continue
            # turn dependency into iterable if necessary
            if not isinstance(depends, list) and not isinstance(depends, tuple):
                depends = [depends]
            # append resource to related dependencies
            for dep in depends:
                deps.setdefault(dep, list()).append(res)
        # XXX: ...

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
        self.depends = None


class JSResource(Resource):
    """A Javascript resource.
    """


class CSSResource(Resource):
    """A CSS Resource.
    """
