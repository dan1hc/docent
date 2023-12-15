import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to PUT."""


@resource.Pets.PUT_ONE(
    errors=[
        FileNotFoundError,
        ]
    )
def update_pet(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> docent.template.package.objects.Pet:  # You MUST annotate the return signature.
    """Update a single pet in the database."""

    if (
        (_id := request.params.get('pet_id'))
        and (pet := docent.template.package.objects.Pet.from_rest(request.body))
        ):
        # Don't forget to set '_id' on pet, it's not in the request body.
        pet: docent.template.package.objects.Pet
        pet._id = _id

        # Update in our 'database'.
        docent.template.package.clients.DatabaseClient.update_one(pet.as_dbo)

        return pet
    else:
        # Raising an exception imported or derived from docent[rest]
        # should automatically include the correct http error code
        # in the resposne.
        raise FileNotFoundError(
            f"Could not find a pet for the provided id: '{_id!s}'."
            )


@resource.Pets.PUT_MANY
def update_pets(
    request: docent.rest.Request
    ) -> list[docent.template.package.objects.Pet]:
    """Update multiple pets in the database."""

    pets = [
        docent.template.package.objects.Pet.from_rest(record)
        for record
        in request.body
        ]

    for pet in pets:
        docent.template.package.clients.DatabaseClient.update_one(pet.as_dbo)

    return pets
