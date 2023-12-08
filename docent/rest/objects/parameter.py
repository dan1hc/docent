__all__ = (
    'Header',
    'Parameter',
    'Parameters',
    )

import dataclasses
import hashlib
import typing

import docent.core

from .. import enums
from .. import utils

from . import base
from . import constants
from . import schema


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class Parameter(base.Component):  # noqa

    name: str = None
    description: str = None
    in_: str = None
    required: bool = False
    schema: dict[str, typing.Any] = dataclasses.field(
        default_factory=dict
        )
    content: base.Content = None
    allowReserved: bool = None

    def __post_init__(self):
        super().__post_init__()
        if '$ref' in self.schema:
            if Constants.FIELD_DELIM not in self.schema['$ref']:
                self.content = base.Content(
                    _name=enums.component.ContentType.json.value,
                    schema=self.schema
                    )
                self.schema = None

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.parameters.value


@dataclasses.dataclass
class Parameters(base.Component):  # noqa

    def __iter__(self) -> typing.Iterator['Parameter']:
        for component in self._extensions:
            yield component

    @property
    def as_reference(self) -> list[dict[str, str]]:  # noqa
        return sorted(
            (
                component.as_reference
                for component
                in self._extensions
                ),
            key=utils.sort_on_last_field
            )

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.parameters.value

    @classmethod
    def from_list(
        cls,
        parameters: list[Parameter],
        ) -> 'Parameters':  # noqa
        return cls(_extensions=parameters)

    @classmethod
    def from_object(
        cls,
        obj: docent.core.objects.DocObject,
        paramater_location: str = enums.parameter.In.query.value,
        method_name: str = None,
        ) -> 'Parameters':  # noqa
        params = []
        schema_obj = schema.SchemaObject.from_object(obj, method_name=method_name)
        properties: dict[str, schema.SchemaComponent] = schema_obj.properties
        for param_name, param_schema in properties.items():
            if (
                paramater_location == enums.parameter.In.query.value
                and param_name.strip('_').endswith('id')
                ):
                continue
            else:
                params.append(
                    Parameter(
                        name=param_name,
                        _name=Constants.FIELD_DELIM.join(
                            (
                                method_name,
                                obj.reference,
                                paramater_location,
                                param_name
                                )
                            ),
                        in_=paramater_location,
                        schema=param_schema.as_reference,
                        required=bool(param_name in (schema_obj.required or []))
                        )
                    )
        return cls(_extensions=params)


@dataclasses.dataclass
class Header(Parameter):  # noqa

    def __hash__(self) -> int:
        return int(
            hashlib.sha1(
                (
                    self._name
                    or self.__class__.__name__
                    ).encode()
                ).hexdigest(),
            base=16
            )

    def __post_init__(self):
        self._name = f'header.{self.name}'
        self.in_= enums.parameter.In.header.value
        self.schema = schema.SchemaComponent(
            type=enums.component.DataType.string.value
            )
        super().__post_init__()

    def __repr__(cls) -> str:
        return cls.as_json
