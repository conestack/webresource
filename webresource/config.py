import logging
import uuid


logger: logging.Logger = logging.getLogger(__name__)
namespace_uuid: uuid.UUID = uuid.UUID('f3341b2e-f97e-40d2-ad2f-10a08a778877')


class ResourceConfig:
    """Config singleton for web resources."""

    development: bool

    def __init__(self) -> None:
        self.development = False


config: ResourceConfig = ResourceConfig()
