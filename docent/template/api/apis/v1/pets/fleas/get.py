import docent.rest
import docent.template.package

from . import constants
from . import resource


class Constants(constants.FleasNameSpaceConstants):
    """Constant values specific only to GET."""


@resource.Fleas.GET_ONE(
    errors=[
        FileNotFoundError,
        ]
    )
def get_flea(
    request: docent.rest.Request
    ) -> docent.template.package.objects.Flea:
    """Retrieve a single flea from the database by identifier."""

    
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
    elif (
        (_id := request.params.get('flea_id'))
        and (flea := docent.template.package.objects.Flea.from_id(_id))
        ):
        return flea
    else:
        raise FileNotFoundError(
            f"Could not find a flea for the provided id: '{_id!s}'."
            )


@resource.Fleas.GET_MANY
def get_fleas(
    request: docent.rest.Request
    ) -> list[docent.template.package.objects.Flea]:
    """Retrieve as many fleas in the database as match the query."""

    
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
    elif not request.params:
        return [
            docent.template.package.objects.Flea.from_dict(record)
            for record
            in docent.template.package.clients.DatabaseClient.DATA.values()
            ]

    return [
        flea
        for record
        in docent.template.package.clients.DatabaseClient.DATA.values()
        if (
            (
                flea := docent.template.package.objects.Flea.from_dict(record)
                )
            and all(
                flea[k] == v
                for k, v
                in request.params.items()
                if k in flea
                )
            )
        ]
