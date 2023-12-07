import warnings

from .. import objects

from . import constants
from . import resource


class Constants(constants.HealthzNameSpaceConstants):
    """Constant values specific only to GET."""


@resource.Healthz.GET_MANY(
    response_headers=Constants.BASE_RESPONSE_HEADERS,
    )
def get_heartbeat(request: objects.Request) -> resource.HeartBeat:
    """Default status check."""

    return resource.HeartBeat()
