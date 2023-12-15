import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to DELETE."""


@resource.Pets.DELETE_ONE(
    errors=[
        FileNotFoundError,
        ]
    )
def delete_pet(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> None:  # `None` indicates an empty response.
    """Remove a single pet from the database."""

    if (_id := request.params.get('pet_id')):
        # Update in our 'database'.
        return docent.template.package.clients.DatabaseClient.delete_one(_id)
    else:
        # Raising an exception imported or derived from docent[rest]
        # should automatically include the correct http error code
        # in the resposne.
        raise FileNotFoundError(
            f"Could not find a pet for the provided id: '{_id!s}'."
            )


@resource.Pets.DELETE_MANY(
    errors=[
        FileNotFoundError,
        ]
    )
def delete_pets(
    request: docent.rest.Request
    ) -> None:
    """Remove as many pets in the database as match the query."""

    pets: list[docent.template.package.objects.Pet] = [
        pet
        for record
        in docent.template.package.clients.DatabaseClient.DATA.values()
        if (
            (
                pet := docent.template.package.objects.Pet.from_dict(record)
                )
            and all(
                pet.as_rest[k] == v
                for k, v
                in request.params.items()
                )
            )
        ]

    if not pets:
        raise FileNotFoundError('Could not find any pets matching the query.')

    for pet in pets:
        docent.template.package.clients.DatabaseClient.delete_one(pet._id)
