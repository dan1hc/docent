import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.FleasNameSpaceConstants):
    """Constant values specific only to DELETE."""


@resource.Fleas.DELETE_ONE(
    errors=[
        FileNotFoundError,
        ]
    )
def delete_flea(
    request: docent.rest.Request
    ) -> None:
    """Remove a single flea from the database."""

    if (_id := request.params.get('flea_id')):
        return docent.template.package.clients.DatabaseClient.delete_one(_id)
    else:
        raise FileNotFoundError(
            f"Could not find a flea for the provided id: '{_id!s}'."
            )


@resource.Fleas.DELETE_MANY(
    errors=[
        FileNotFoundError,
        ]
    )
def delete_fleas(
    request: docent.rest.Request
    ) -> None:
    """Remove as many fleas in the database as match the query."""

    fleas: list[docent.template.package.objects.Flea] = [
        flea
        for record
        in docent.template.package.clients.DatabaseClient.DATA.values()
        if (
            (
                flea := docent.template.package.objects.Flea.from_dict(record)
                )
            and all(
                flea.as_rest[k] == v
                for k, v
                in request.params.items()
                )
            )
        ]

    if not fleas:
        raise FileNotFoundError('Could not find any fleas matching the query.')

    for flea in fleas:
        docent.template.package.clients.DatabaseClient.delete_one(flea._id)
