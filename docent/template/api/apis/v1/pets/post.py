import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to POST."""


@resource.Pets.POST_MANY(
    authorizers=Constants.DEFAULT_AUTHORIZERS,
    request_headers=Constants.DEFAULT_REQUEST_HEADERS,
    response_headers=Constants.DEFAULT_RESPONSE_HEADERS,
    )
def create_pets(
    request: docent.rest.Request  # The function should only ever take an docent.rest.Request
    ) -> list[docent.template.package.objects.Pet]:  # You MUST annotate the return signature.
    """Add new pets to the database."""

    # Instantiate a new Pet object from the request's body.
    #
    # We can safely assume the operation will succeed.
    # The request will have already been validated
    # against the object's fields' data types and 
    # any additional requirements specified in field metadata
    # by this point.
    pets = [
        docent.template.package.objects.Pet.from_rest(record)
        for record
        in request.body
        ]

    # Insert the new, valid Pet object into our database.
    #
    # As you should be able to see from hovering over the
    # 'insert_one' method of the 'DatabaseClient' class below,
    # our particular database / client automatically generates
    # an id, in this case called '_id', and returns the
    # successfully inserted object as a dictionary, including its
    # newly filled '_id' key, the value assigned by the database.
    dbos = [
        docent.template.package.clients.DatabaseClient.insert_one(pet.as_dbo)
        for pet
        in pets
        ]

    # Since docent[rest] expects an DocObject, a list[DocObject],
    # or a typing.Union of any DocObject, list[DocObject] thereof,
    # we need to convert the raw python dictionary returned by
    # our database client back into an DocObject derivative (our Pet)
    # before returning it.
    return [
        docent.template.package.objects.Pet.from_dict(dbo)
        for dbo
        in dbos
        ]
