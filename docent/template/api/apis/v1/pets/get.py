import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to GET."""


@resource.Pets.GET_ONE(
    authorizers=Constants.DEFAULT_AUTHORIZERS,
    request_headers=Constants.DEFAULT_REQUEST_HEADERS,
    response_headers=Constants.DEFAULT_RESPONSE_HEADERS,
    errors=[
        FileNotFoundError,
        ]
    )
def get_pet(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> docent.template.package.objects.Pet:  # You MUST annotate the return signature.
    """Retrieve a single pet from the database by identifier."""

    if (
        (_id := request.params.get('pet_id'))
        and (pet := docent.template.package.objects.Pet.from_id(_id))
        ):
        # If a valid '_id' was supplied, for which we could
        # successfully find a corresponding pet in our database,
        # return the pet.
        return pet
    else:
        # Raising an exception imported or derived from docent[rest]
        # should automatically include the correct http error code
        # in the resposne.
        raise FileNotFoundError(
            f"Could not find a pet for the provided id: '{_id!s}'."
            )


@resource.Pets.GET_MANY(
    authorizers=Constants.DEFAULT_AUTHORIZERS,
    request_headers=Constants.DEFAULT_REQUEST_HEADERS,
    response_headers=Constants.DEFAULT_RESPONSE_HEADERS,
    )
def get_pets(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> list[docent.template.package.objects.Pet]:  # You MUST annotate the return signature.
    """Retrieve as many pets in the database as match the query."""

    if not request.params:
        return [
            docent.template.package.objects.Pet.from_dict(record)
            for record
            in docent.template.package.clients.DatabaseClient.DATA.values()
            ]

    return [
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
