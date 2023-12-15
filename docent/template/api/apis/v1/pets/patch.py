import typing

import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to PATCH."""


@resource.Pets.PATCH_ONE(
    errors=[
        FileNotFoundError,
        ]
    )
def update_pet(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> docent.template.package.objects.Pet:  # You MUST annotate the return signature.
    """Update a single pet's properties in the database."""

    if (
        (_id := request.params.get('pet_id'))
        and (pet := docent.template.package.objects.Pet.from_id(_id))
        ):

        # Take advantage of DocObject special methods like `-`,
        # which will calculate the 'difference' between two
        # DocObjects (in this case, the incumbent and a pet
        # as specified by the request's query parameters).
        diff: dict[str, typing.Any] = (
            pet
            - docent.template.package.objects.Pet.from_rest(request.params)
            )

        # Skip '_id' diff.
        for k, v in diff.items():
            if k in request.params:
                setattr(pet, k, v)

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
