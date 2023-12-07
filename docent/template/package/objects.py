import dataclasses

import docent.core

from . import clients
from . import enums


@dataclasses.dataclass
class Pet(docent.core.DocObject):
    """
    A simple pet that makes for a good example.

    * This python docstring will be parsed as the default description \
    for its corresponding RESTful resource if no docstring for \
    the docent.rest.Resource itself is provided.

    * It will always be parsed as the description / docstring for the \
    Pet object itself in all auto-generated documentation.

    * It will be rendered in [markdown](https://www.markdownguide.org/cheat-sheet/).

    ---

    Requirements
    ------------

    * A pet's name can always be changed after its creation, but \
    the type of an existing pet cannot be changed.

    * However, an existing pet can always be exchanged for \
    another pet of a different name and type, \
    so long as a valid identifier is provided to \
    identify the existing pet for replacement.

    ---

    Additional Requirements
    -----------------------

    Allowed types:

    ```py
    ['cat', 'dog', 'turtle']
    ```

    """

    # I was five years old when my parents let the youngest of 
    # their four children name the family's new dog.
    #
    # Their mistake.
    #
    # Continue reading to see an example implementation of the above
    # product requirements for pet resource management and learn
    # how you can avoid making the same mistake as my parents
    # by restricting user input so no pet will ever again
    # be called "Mr. James Gak".

    _id: str = None  # Broadly speaking, DocObjects should be 1:1 with
                     # a record in a data store. This generally means
                     # they should have a unique identifier (example: '_id').

    name: str = dataclasses.field(
        default='Fido',
        metadata={
            'maxLength': 32,  # No pet should need a name longer than
                              # 32 characters.
            'minLength': 2,  # No one-letter names.
            'pattern': '[A-Z]{1}[a-z]+',  # Force to match a regex pattern
                                          # to only accept single-word,
                                          # alpha-character names in
                                          # Proper CamelCase.
            'required': {
                'post',  # Do not let users create pets without names.
                'put',   # They also are not allowed to exchange their
                         # pet without specifying a name for the new pet.
                }
            }
        )

    type: str = dataclasses.field(
        default=None,  # A default value must be specified. If the default
                       # value is mutable (ex. a list), a 'default_factory'
                       # function that returns the value must be specified
                       # instead of the value itself.
                       # (ex. default_factory=lambda: [] will work
                       # default=[] will raise an error).
        metadata={
            'enum': enums.ValidPetTypes,  # Specify an enum 
                                          # (or another container, ex. a list)
                                          # to restrict the allowed values
                                          # for the field to the container's
                                          # elements.
            'ignore': {
                'patch',  # Ignore user input for this field, for
                          # this method. In this case, users will be
                          # unable to modify an existing pet's 'type',
                          # even if they correctly specify a valid value
                          # for it in the request's query parameters.
                },
            'nullable': False,  # Restrict the field from being empty
                                # for ANY available methods not otherwise
                                # ignored.
                                # 
                                #   Note: if the field's default value is 
                                #   'None' (as above), this will only apply
                                #   to scenarios where the user actually
                                #   tried to explicitly pass a null value
                                #   to this field in the request.
                                # 
            'required': {
                'post',  # Require the user to specify a value for this
                'put',   # field on all POST and PUT requests.
                }
            }
        )

    @classmethod
    def from_id(cls, _id: str) -> 'Pet':
        """
        Return an instantiated Pet object from database by id.
    
        If no pet is returned from the database, an empty Pet \
        will be returned instead.

        ---

        This python docstring will be ignored by SwaggerUI, \
        but it will be included in any wiki documentation generated \
        by Sphinx.

        * Our recommendation is that your wiki documentation \
        be reserved for internal maintainers, while your SwaggerUI \
        be made the primary documentation resource for all \
        intended consumers of the API.

        * It follows then that you should define and document the logic \
        that alters or retrieves an object in its data store on a method \
        like the below, rather than on the DocObject's docstring itself. \
        See example below.

        ```py
        @classmethod
        def from_id(cls, _id: str) -> 'Pet':
            \"""
            Return an instantiated Pet object from database by id.

            If no pet is returned from the database, an empty Pet
            will be returned instead.
            \"""

            return cls(
                **(
                    clients.DatabaseClient.find_one(_id)
                    or {}
                    )
                )

        ```

        """

        return cls(**(clients.DatabaseClient.find_one(_id) or {}))
