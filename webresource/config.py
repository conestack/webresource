import logging
import uuid


logger = logging.getLogger(__name__)
namespace_uuid = uuid.UUID('f3341b2e-f97e-40d2-ad2f-10a08a778877')


class ResourceConfig(object):
    """Config singleton for web resources."""

    def __init__(self):
        self.development = False


config = ResourceConfig()
