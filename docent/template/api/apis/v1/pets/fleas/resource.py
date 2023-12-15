__all__ = (
    'Fleas',
    )

import docent.rest
import docent.template.package

from .. import resource

from . import constants


class Constants(constants.FleasNameSpaceConstants):
    """Constant values specific only to the Fleas resource."""


@docent.rest.API(
    include_enums_endpoint=True,
    )
class Fleas(resource.Pets):  # noqa

    @classmethod
    @property
    def resource(cls) -> docent.template.package.objects.Flea:  # noqa
        return docent.template.package.objects.Flea
