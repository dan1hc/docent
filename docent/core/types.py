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
from . import utils


class Constants(constants.PackageConstants):  # noqa

    FORBIDDEN_OBJECTS: set[str] = {
        'DocObject',
        }


class DocField:
    """
    Simple docent field object.

    ---

    Facilitates downstream query operations by making
    available __special_method__ implementations where
    they would otherwise be restricted by dataclasses.Field's
    __setattribute__ method.

    """

    def __init__(self, name: str, type: object):
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
        """Instantiate DocField from a dataclasses.Field instance."""

        return cls(field.name, field.type)


class DocMeta(abc.ABCMeta, type):
    """DocObject class constructor."""

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def APPLICATION_OBJECTS(cls) -> dict[str, 'objects.DocObject']:
        """Python dict containing all DocObject subclasses used by the program."""  # noqa

        return {}

    def __call__(cls, *args, **kwargs):
        """Register a DocObject derivative as an application object."""

        if not cls.__module__.startswith('docent.core'):
            cls.APPLICATION_OBJECTS.setdefault(cls.reference, cls)

        return super().__call__(*args, **kwargs)

    def __contains__(cls, key: str) -> bool:
        """Return True if key (or alias) is a field for the DocObject derivative."""  # noqa

        return bool(cls.key_for(key))

    def __getattribute__(cls, __name: str) -> typing.Union[DocField, typing.Any]:  # noqa
        """Return DocField instead of field value for uninstantiated DocObject derivatives."""  # noqa

        if (
            (type(cls) is DocMeta)
            and (
                object.__getattribute__(cls, '__name__')
                not in Constants.FORBIDDEN_OBJECTS
                )
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

    def __getitem__(cls, key: str) -> typing.Any:
        """Return field value dict style."""

        if (k := cls.key_for(key)):
            return cls.__dict__.get(k)
        else:
            raise KeyError(key)

    def __setitem__(cls, key: str, value: typing.Any):
        """Set field value dict style."""

        if (k := cls.key_for(key)):
            setattr(cls, k, value)
        else:
            raise KeyError(key)

    @functools.cache
    def key_for(cls: 'objects.DocObject', key: str) -> typing.Union[str, None]:  # noqa
        """
        Get the actual attribute name for key as it has been
        assigned to the DocObject derivative.

        ---

        For example, the below would return '_id', the real
        field name for the otherwise friendly alias, 'id'.

        ```py
        import docent.template.package

        docent.template.package.objects.Pet.key_for('id')
        >>>
        '_id'

        ```

        """

        if (
            cls.is_snake_case
            and not key.islower()
            and (
                (
                    k := (
                        _k := utils.camel_case_to_snake_case(
                            key.strip('_')
                            )
                        )
                    ) in cls.fields
                or (k := '_' + _k) in cls.fields
                or (k := _k + '_') in cls.fields
                or (k := '_' + _k + '_') in cls.fields
                )
            ):
            return k
        elif (
            (k := (_k := key.strip('_'))) in cls.fields
            or (k := '_' + _k) in cls.fields
            or (k := _k + '_') in cls.fields
            or (k := '_' + _k + '_') in cls.fields
            ):
            return k
