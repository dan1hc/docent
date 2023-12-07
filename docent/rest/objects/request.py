__all__ = (
    'Request',
    'RequestBody',
    )

import dataclasses
import typing

import docent.core

from .. import enums

from . import base
from . import constants
from . import schema


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class Request(docent.core.objects.DocObject):  # noqa

    body: typing.Any = dataclasses.field(
        default_factory=dict
        )
    headers: dict[str, typing.Any] = dataclasses.field(
        default_factory=dict
        )
    method: str = None
    path: str = None
    params: dict[str, typing.Any] = dataclasses.field(
        default_factory=dict
        )

    @property
    def path_as_list(self) -> list[str]:  # noqa
        return [
            s
            for s
            in self.path.split('/')
            if s
            ]

    def __post_init__(self):  # noqa
        if self.path:
            self.path = self.path.strip('/')


@dataclasses.dataclass
class RequestBody(base.Component):  # noqa

    required: bool = True
    description: str = None
    content: base.Content = None

    def __bool__(self) -> bool:
        return bool(self.content)

    @classmethod
    def from_object(
        cls,
        obj: typing.Union[
            docent.core.objects.DocObject,
            list[docent.core.objects.DocObject]
            ],
        content_type: str = enums.component.ContentType.json.value,
        description: str = None,
        required: bool = True,
        method_name: str = None,
        ) -> 'RequestBody':  # noqa
        return cls(
            _name=Constants.DOC_DELIM.join(
                (
                    (method_name or 'base'),
                    'many' if (
                        a := (
                            hasattr(obj, '__args__')
                            and not isinstance(
                                obj,
                                typing._UnionGenericAlias
                                )
                            )
                        ) else 'one',
                    obj.__args__[0].reference if a else obj.reference
                    )
                ),
            content=base.Content(
                _name=content_type,
                schema=schema.SchemaComponent.from_py_type(
                    obj,
                    method_name=method_name,
                    ).as_reference
                ),
            description=description,
            required=required
            )

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.requestBodies.value
