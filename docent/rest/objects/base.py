__all__ = (
    'Component',
    'ComponentMeta',
    'Content',
    )

import dataclasses
import hashlib
import json
import typing

import docent.core

from .. import utils

from . import constants


class Constants(constants.ComponentConstants):  # noqa

    pass


class ComponentMeta(docent.core.types.DocMeta):  # noqa

    APPLICATION_COMPONENTS: dict[str, dict[str, 'Component']] = {}


@dataclasses.dataclass
class Component(metaclass=ComponentMeta):  # noqa

    _name: str = None
    _extensions: list['Component'] = dataclasses.field(
        default_factory=list
        )

    def __init_subclass__(cls) -> None:


        def __hash__(cls) -> int:
            return int(
                hashlib.sha1(
                    (
                        cls._name
                        or cls.__class__.__name__
                        ).encode()
                    ).hexdigest(),
                base=16
                )


        if not hasattr(cls, '__hash__') or cls.__hash__ is None:
            cls.__hash__ = __hash__


        def __repr__(cls) -> str:
            return cls.as_json


        cls.__repr__ = __repr__

        return super().__init_subclass__()

    def __post_init__(self):
        self._extensions = sorted(self._extensions)
        if (
            self.component_type
            and isinstance(self.as_reference, dict)
            and (
                (ref := self.as_reference.get('$ref'))
                or (
                    ref := self.as_reference.get(
                        self.component_type[:-1],
                        {}
                        ).get('$ref')
                    )
                )
            and ref not in self.__class__.APPLICATION_COMPONENTS.get(
                self.component_type,
                {}
                )
            ):
            self.__class__.APPLICATION_COMPONENTS.setdefault(
                self.component_type,
                {}
                )
            self.__class__.APPLICATION_COMPONENTS[
                self.component_type
                ][ref] = self

    def __add__(self, other: 'Component') -> 'Component':
        extended = self.__class__(
            **{
                k: v
                for k, v
                in self.__dict__.items()
                if k in self.__dataclass_fields__
                },
            )
        extended._extensions = list(set(self._extensions + other._extensions))
        return extended

    def __lt__(self, other: 'Component') -> bool:
        if self._name and other._name:
            return self._name < other._name
        elif self._name:
            return self._name < other.__class__.__name__
        elif other._name:
            return self.__class__.__name__ < other._name
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def __gt__(self, other: 'Component') -> bool:
        if self._name and other._name:
            return self._name > other._name
        elif self._name:
            return self._name > other.__class__.__name__
        elif other._name:
            return self.__class__.__name__ > other._name
        else:
            return self.__class__.__name__ > other.__class__.__name__

    def __bool__(self) -> bool:
        return bool(self._extensions)

    def __iadd__(self, other: 'Component'):
        return self + other

    def __iter__(self) -> typing.Iterator['Component']:
        for component in self._extensions:
            yield component

    def _to_component(self) -> dict[str, typing.Any]:
        d = {
            k: v
            for k, v
            in self.__dict__.items()
            if not k.startswith('_')
            and v is not None
            }
        dbo = {}
        for k in sorted(d, key=utils.sort_on_last_field):
            v = d[k]
            if k.endswith('_'):
                k = k[:-1]
            if isinstance(v, (Component, ComponentMeta)):
                dbo[k] = v.as_reference
            elif isinstance(v, dict):
                v: dict[str, typing.Any]
                dbo[k] = {
                    _k: (
                        _v.as_reference
                        if
                        isinstance((_v := v[_k]), (Component, ComponentMeta))
                        else
                        _v
                        )
                    for _k
                    in sorted(v, key=utils.sort_on_last_field)
                    }
            elif isinstance(v, list) and not isinstance(v, str):
                dbo[k] = sorted(
                    (
                        _v.as_reference
                        if
                        isinstance(_v, (Component, ComponentMeta))
                        else
                        _v
                        for _v
                        in v
                        ),
                    key=utils.sort_on_last_field
                    )
            else:
                dbo[k] = v
        return dbo

    @property
    def component_type(self) -> str:  # noqa
        raise NotImplementedError(
            ' '.join(
                (
                    'Must implement a property returning',
                    'one of the ComponentType enums or None.'
                    )
                )
            )

    @property
    def as_component(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = self._to_component()
        for component in self._extensions:
            d.update(component.as_component)
        if self._name:
            return {self._name: d}
        else:
            return d

    @property
    def as_reference(self) -> dict[str, str]:  # noqa
        if self._name and self.component_type:
            ref = '/'.join(
                (
                    '#',
                    'components',
                    self.component_type,
                    self._name
                    )
                )
            return {'$ref': utils.filter_component_uri(ref)}
        else:
            return self.as_component

    @property
    def as_json(self) -> str:
        """Return object as a JSON serialized string."""

        return json.dumps(self.as_component, default=str, indent=2)


@dataclasses.dataclass
class Content(Component):  # noqa

    schema: dict = None

    def __bool__(self) -> bool:
        return bool(self.schema)

    @property
    def component_type(self) -> None:  # noqa
        return None
