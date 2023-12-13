__all__ = (
    'DocField',
    'DocMeta',
    )

import abc
import dataclasses
import functools
import json
import typing

from . import constants
from . import objects


class Constants(constants.PackageConstants):  # noqa

    pass


class DocField:
    """
    Simple docent field object.

    ---

    Facilitates downstream query operations by making
    available __special_method__ implementations where
    they would otherwise be restricted by dataclasses.Field's
    __setattribute__ method.

    """

    def __init__(self, name: str, type: typing.Type):
        self.name = name
        self.type = type

    def __repr__(self) -> str:
        return json.dumps(
            {
                'name': self.name,
                'type': self.type
                },
            default=str,
            indent=Constants.INDENT
            )

    def __eq__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__eq__': value}}

    def __ne__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__ne__': value}}

    def __gt__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__gt__': value}}

    def __gte__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__gte__': value}}

    def __lt__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__lt__': value}}

    def __lte__(self, value: typing.Any) -> dict[str, dict[str, typing.Any]]:
        return {self.name: {'__lte__': value}}

    @classmethod
    def from_dataclass_field(cls, field: dataclasses.Field) -> 'DocField':
        """Instantiate DocField from dataclasses field."""

        return cls(field.name, field.type)


class DocMeta(abc.ABCMeta, type):  # noqa

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def APPLICATION_OBJECTS(cls) -> dict[str, 'objects.DocObject']:  # noqa
        return {}

    def __call__(cls, *args, **kwargs):
        if (
            not cls.__module__.startswith('docent.core')
            and not cls.__module__.startswith('docent.rest')
            ):
            cls.APPLICATION_OBJECTS.setdefault(cls.reference, cls)
        return super().__call__(*args, **kwargs)

    def __getattribute__(cls, __name: str) -> typing.Any:
        if (
            (type(cls) is not type)
            and object.__getattribute__(cls, '__name__') != 'DocObject'
            and (
                field := (
                    super()
                    .__getattribute__('__dataclass_fields__')
                    .get(__name)
                    )
                )
            ):
            return DocField.from_dataclass_field(field)
        else:
            return super().__getattribute__(__name)
