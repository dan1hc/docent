__all__ = (
    'Authorizer',
    )

import dataclasses
import typing

from .. import enums

from . import base
from . import constants


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class Authorizer(base.Component):  # noqa

    name: str = None
    in_: str = None
    type: str = None

    def __post_init__(self):
        self._name = self._name or f'{self.name.lower()}-authorizer'
        super().__post_init__()

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.securitySchemes.value

    @property
    def as_component(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = self._to_component()
        for component in self._extensions:
            d.update({component._name: component.as_reference})
        if self._name:
            return {self._name: d}
        else:
            return d
