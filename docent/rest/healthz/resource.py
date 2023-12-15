__all__ = (
    'Healthz',
    )

import dataclasses

import docent.core

from .. import resource
from .. import api

from . import constants


class Constants(constants.HealthzNameSpaceConstants):
    """Constant values specific only to the Healthz resource."""


@dataclasses.dataclass
class HeartBeat(docent.core.objects.DocObject):
    """Default application heartbeat."""

    status: str = dataclasses.field(
        default='OK',
        metadata={
            'ignore': True,
            }
        )


@api.API
class Healthz(resource.Resource):  # noqa

    @classmethod
    @property
    def resource(cls) -> HeartBeat:  # noqa
        return HeartBeat
