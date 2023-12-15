import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.FleasNameSpaceConstants):
    """Constant values specific only to POST."""


@resource.Fleas.POST_MANY(
    errors=[
        FileNotFoundError,
        ]
    )
def create_fleas(
    request: docent.rest.Request
    ) -> list[docent.template.package.objects.Flea]:
    """Add new fleas to the database."""

    if (
        (pet_id := request.params['pet_id'])
        and not (
            docent.
            template.
            package.
            clients.
            DatabaseClient.find_one(pet_id)
            )
        ):
        raise FileNotFoundError(
            f"Could not find a pet for the provided id: '{pet_id!s}'."
            )

    fleas: list[docent.template.package.objects.Flea] = [
        docent.template.package.objects.Flea.from_rest(record)
        for record
        in request.body
        ]
    for flea in fleas:
        flea.pet_id = pet_id

    dbos = [
        docent.template.package.clients.DatabaseClient.insert_one(flea.as_dbo)
        for flea
        in fleas
        ]

    return [
        docent.template.package.objects.Flea.from_dict(dbo)
        for dbo
        in dbos
        ]
