__all__ = (
    'Healthz',
    )

import dataclasses

import docent.core

from .. import resource
from .. import route

from . import constants


class Constants(constants.HealthzNameSpaceConstants):
    """Constant values specific only to the Healthz resource."""


@dataclasses.dataclass
class HeartBeat(docent.core.DocObject):
    """Default application heartbeat."""

    status: str = dataclasses.field(
        default='OK',
        metadata={
            'ignore': True,
            }
        )


@route.Route
class Healthz(resource.Resource):  # noqa

    @classmethod
    @property
    def resource(cls) -> HeartBeat:  # noqa
        return HeartBeat
