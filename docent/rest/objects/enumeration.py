__all__ = (
    'Enumeration',
    )

import dataclasses

import docent.core


@dataclasses.dataclass
class Enumeration(docent.core.objects.DocObject):
    """Contains all documented object enums."""

    name: str = dataclasses.field(
        default=None,
        metadata={
            'ignore': True,
            }
        )
    values: list = dataclasses.field(
        default_factory=list,
        metadata={
            'ignore': True,
            }
        )
