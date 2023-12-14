__all__ = (
    'Pets',
    )

import docent.rest
import docent.template.package

from . import constants


class Constants(constants.PetsNameSpaceConstants):
    """Constant values specific only to the Pets resource."""


@docent.rest.Route(
    include_enums_endpoint=True,
    )
class Pets(docent.rest.Resource):
    """
    An example of a docent RESTful resource to manage pets.

    * This python docstring will populate the RESTful resource's \
    "Details" section, overriding all other descriptions \
    and / or docstrings.

    * The first line of this docstring will become the summary for the \
    RESTful resource.

    * It will be rendered in [markdown](https://www.markdownguide.org/cheat-sheet/).

    ---

    Requirements
    ------------

    * A pet's name can always be changed after its creation, but \
    the type of an existing pet cannot be changed.

    * However, an existing pet can always be exchanged for \
    another pet of a different name and type, so long as a \
    valid identifier is provided to identify the existing pet \
    for replacement.

    ---

    Additional Requirements
    -----------------------

    Allowed pet types:

    ```py
    ['cat', 'dog', 'turtle']
    ```

    """

    PATH_PREFICES = Constants.DEFAULT_PREFICES

    @classmethod
    @property
    def resource(cls) -> docent.template.package.objects.Pet:  # noqa
        return docent.template.package.objects.Pet
