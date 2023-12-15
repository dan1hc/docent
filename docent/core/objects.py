__all__ = (
    'DocObject',
    'DocRecords',
    )

import abc
import dataclasses
import enum
import functools
import json
import re
import typing

from . import constants
from . import exceptions
from . import types
from . import utils


class Constants(constants.PackageConstants):  # noqa

    pass


@dataclasses.dataclass
class DocObject(metaclass=types.DocMeta):
    """
    Base docent Object.

    ---

    Usage
    -----

    * Subclass to create objects for your application.

    * Ideally, objects should be 1:1 with their counterparts in the \
    data store from which they are originally sourced (even \
    if that data store is your own database, and even if that \
    data is not ostensibly stored in a 1:1 manner, as is the case \
    with most relational databases).
        \
        * For example, if there is a SQL table called `pets` \
        with the schema below, you would want to create \
        a corresponding `python representation` similar to \
        the following.

    #### pets table

    ```
    | id  | name     | type   |
    | --- | -------- | ------ |
    | a1  | fido     | dog    |
    | a2  | garfield | cat    |
    | a3  | sophie   | dog    |
    | a4  | stripes  | turtle |
    ```

    #### python representation

    ```py
    import dataclasses

    import docent.core


    @dataclasses.dataclass
    class Pet(docent.core.DocObject):
        \"""A pet.\"""

        id_: str = None  # Trailing underscores are special
                         # in docent, check the documentation
                         # below for more detail.
        name: str = None
        type: str = None

    ```

    * Implement methods on your object to manage its retrieval and state.

    ```py
    import dataclasses

    import docent.core

    from .. import clients


    @dataclasses.dataclass
    class Pet(docent.core.DocObject):
        \"""A pet.\"""

        id_: str = None
        name: str = None
        type: str = None

        @classmethod
        def get(cls, id_: str) -> 'Pet':
            \"""Find one pet by id.\"""

            return cls(**clients.sql_client.query.where(id=id_))

        def update(self) -> None:
            \"""Update this pet in database.\"""

            clients.sql_client.update(self.as_dbo).where(id=self.id_)

    ```

    * Sometimes one object may technically be the combination of many \
    smaller components. In this case, implement methods like 'get' \
    and 'update' to correctly combine and update the many components.
        \
        * The ONLY items that should be persisted to data storage \
        for the larger, combined object should be properties that \
        are unique to it. Those which are already persisted for \
        constituent pieces in different locations should NOT be \
        re-persisted with the combination object simply because they \
        are components of it.

    ---

    Special Rules
    -------------

    #### Mandatory Default Values
    Subclassed (derivative) objects must include default values for \
    all dataclass fields.

    #### Mandatory Type Annotations
    Type annotations are required as well. This includes annotations for \
    list item elements, tuple elements, dict elements, etc.

    * These are leveraged by downstream programs (docent[rest] among others) \
    to do things like auto-document and auto-generate API's.

    #### Uniform Casing
    ALL Fields must be either camelCase or snake_case, with the only \
    exception being that fields may begin with an underscore '_', so long \
    as all following characters adhere to camelCase or snake_case conventions.

    #### Underscore Prefix for Private Fields
    Fields that begin with an underscore '_' will be ignored on \
    conversion to / from DBO, REST, and JSON representations, \
    unless the field ends with 'id' or 'id_' (case insensitive), \
    in which case it will still be converted.

    * This follows the broader pattern of flagging methods and \
    attributes as private / internal to a system with a preceding \
    underscore. It should be expected that end users of your \
    system will not need to interact with these fields.

    #### Underscore Suffix for Reserved Keyword Fields
    Fields with a trailing underscore '_' will automatically have \
    the trailing underscore removed on conversion to / from \
    DBO, REST, and JSON representations.

    * This allows for python keywords, such as 'in_', to be used \
    as object fields, where they would otherwise raise errors \
    without the proceeding underscore.

    * On translation back using the 'from_dict' and 'from_rest' \
    methods, dictionary keys without underscores will still be \
    checked against these fields -- so, a dictionary with key \
    'in' will correctly map to the 'in_' field on the \
    DocObject. See below for more detail.

    ```py
    import dataclasses

    import docent.core


    @dataclasses.dataclass
    class Pet(docent.core.DocObject):
        \"""A pet.\"""

        id_: str = None
        _alternate_id: str = None

        name: str = None
        type: str = None
        in_: str = None
        is_tail_wagging: bool = True


    # This means the below will work.
    bob_the_dog = Pet.from_dict(
        {
            'id': 'abc123',
            '_alternate_id': 'dog1',
            'name': 'Bob',
            'type': 'dog',
            'in': 'timeout',
            'is_tail_wagging': False
            }
        )

    # And so would this, since the 'from_rest'
    # method automatically converts camelCase to
    # snake_case for all DocObjects with snake_case
    # fields.
    bob_the_dog = Pet.from_rest(
        {
            'id': 'abc123',
            'alternateId': 'dog1',
            'name': 'Bob',
            'type': 'dog',
            'in': 'timeout',
            'isTailWagging': False
            }
        )

    # But to instantiate directly, you
    # would need to include any suffices
    # and ensure correct casing.
    bob_the_dog = Pet(
        id_='abc123',
        _alternate_id='dog1',
        name='Bob',
        type='dog',
        in_='timeout',
        is_tail_wagging=False
        )

    ```

    #### Dataclass Metadata
    The keyword argument 'metadata' can be passed (usually as a dict) to \
    any dataclass field to specify additional, optional information about the \
    object. In certain distributions, this optional information can add utility.

    * For example, docent[rest] will search for keywords like \
    'required' and 'enum' within provided metadata to automatically \
    translate (or 'ignore') additional requirements about the object \
    into an Open API specification.

    ---

    Special Method Usage
    --------------------

    ```py
    if DocObject:
    ```

    DocObject truthiness will evaluate to True if any values for \
    the DocObject instance are different from default values, \
    otherwise False.

    ```py
    print(DocObject)
    ```

    DocObjects are designed to display themselves as neatly \
    formatted JSON on calls to `__repr__`.

    ```py
    DocObject1 << DocObject2
    ```

    Updates DocObject1 with values from DocObject2 if they \
    are a non-default value for the object.

    ```py
    DocObject1 >> DocObject2
    ```

    Overwrites DocObject1 values with those from DocObject2 \
    if they are a non-default value for the object.

    ```py
    DocObject1 - DocObject2
    ```

    Returns a dictionary with {fieldName: fieldValue2} for \
    any fields that differ between the two DocObjects.

    ```py
    value = DocObject['field']
    ```

    Get value for DocObject field.

    ```py
    DocObject['field'] = value
    ```

    Set value for DocObject field.

    ```py
    field in DocObject
    ```

    Returns True if any one of field, _field, field_, or _field_
    is a valid field for the DocObject, otherwise False.

    """

    def __init_subclass__(cls):
        if cls.fields and not any((cls.isCamelCase, cls.is_snake_case)):
            raise exceptions.IncorrectCasingError(
                ' '.join(
                    (
                        'All fields for all DocObject derivatives',
                        'must be either snake_case or camelCase.'
                        f'\nFIELDS: {sorted(cls.fields)!s}',
                        )
                    )
                )
        field_meta: dataclasses.Field
        for field_meta in cls.fields.values():
            if (
                isinstance(field_meta.default, dataclasses._MISSING_TYPE)
                and isinstance(
                    field_meta.default_factory,
                    dataclasses._MISSING_TYPE
                    )
                ):
                raise exceptions.MissingDefaultValueError(
                    ' '.join(
                        (
                            'All DocObject derivatives must',
                            'include a default value',
                            'for all dataclass fields.',
                            f'\nFIELD: {field_meta.name}',
                            )
                        )
                    )
            elif (
                isinstance(field_meta.type, (dict, list, tuple, set))
                and not isinstance(field_meta.type, str)
                and not hasattr(field_meta.type, '__args__')
                ):
                raise exceptions.MissingContainerTypeAnnotation(
                    ' '.join(
                        (
                            'All dict, list, set, and tuple fields'
                            'on DocObject derivatives must',
                            'include element datatype annotations.',
                            f'\nFIELD: {field_meta.name}',
                            )
                        )
                    )

        if (
            not cls.__module__.startswith('docent.core')
            and not cls.__module__.startswith('docent.rest')
            ):
            cls.APPLICATION_OBJECTS.setdefault(cls.reference, cls)

        def __repr__(self) -> str:
            return json.dumps(
                self.as_rest,
                default=utils.prefix_value_to_string,
                indent=Constants.INDENT,
                sort_keys=True
                )

        cls.__repr__ = __repr__

        return super().__init_subclass__()

    def __bool__(self) -> bool:
        """Determine object truthiness by diff with default field values."""  # noqa

        return bool(self - self.__class__())

    def __contains__(self, key: str) -> bool:
        """Return True if key (or alias) is a field for the DocObject derivative."""  # noqa

        return bool(self.__class__.key_for(key))

    def __getitem__(self, key: str) -> typing.Any:
        """Return field value dict style."""

        if (k := self.__class__.key_for(key)):
            return self.__dict__[k]
        else:
            raise KeyError(key)

    def __setitem__(self, key: str, value: typing.Any):
        """Set field value dict style."""

        if (k := self.__class__.key_for(key)):
            setattr(self, k, value)
        else:
            raise KeyError(key)

    def __sub__(self, other: 'DocObject') -> dict[str, typing.Any]:
        """Calculate diff between same object types."""

        diff = {}
        for field in self.fields:
            value = self[field]
            other_value = other[field]
            if (
                isinstance(value, DocObject)
                and isinstance(other_value, DocObject)
                and value.as_dbo != other_value.as_dbo
                ):
                diff[field] = other_value
            elif value != other_value:
                diff[field] = other_value
        return diff

    def __lshift__(self, other: 'DocObject') -> 'DocObject':
        """Interpolate values from other if populated with non-default."""

        obj = other.__class__()
        for field, field_meta in self.fields.items():
            value = self[field]
            other_value = other[field]
            if isinstance(
                field_meta.default_factory,
                dataclasses._MISSING_TYPE
                ):
                default_value = field_meta.default
            else:
                default_value = field_meta.default_factory()
            if value != default_value:
                obj[field] = value
            elif other_value != default_value:
                obj[field] = other_value
            else:
                obj[field] = value
        return obj

    def __rshift__(self, other: 'DocObject') -> 'DocObject':
        """Overwrite values with other if populated with non-default."""

        obj = other.__class__()
        for field, field_meta in self.fields.items():
            value = self[field]
            other_value = other[field]
            if isinstance(
                field_meta.default_factory,
                dataclasses._MISSING_TYPE
                ):
                default_value = field_meta.default
            else:
                default_value = field_meta.default_factory()
            if other_value != default_value:
                obj[field] = other_value
            else:
                obj[field] = value
        return obj

    def _to_dbo(
        self,
        camel_case: bool = False,
        include_null: bool = True,
        ) -> typing.Union[dict, list[dict]]:
        d = {
            k: v
            for k, v
            in self.__dict__.items()
            if (
                k.removesuffix('_').lower().endswith('id')
                or not k.startswith('_')
                )
            and (
                v is not None
                if not include_null
                else True
                )
            and (
                not isinstance(
                    getattr(self.__class__, k),
                    functools.cached_property
                    )
                if hasattr(self.__class__, k)
                else True
                )
            }
        dbo: dict[str, typing.Any] = {}
        for k, v in d.items():
            if isinstance(v, DocObject):
                dbo[k] = v._to_dbo(camel_case, include_null)
            elif isinstance(v, dict):
                v: dict[str, typing.Any]
                dbo[k] = {
                    (
                        utils.to_camel_case(_k.strip('_'))
                        if camel_case
                        else _k
                        ): (
                            _v._to_dbo(camel_case, include_null)
                            if isinstance(_v, DocObject)
                            else
                            _v
                            )
                    for _k, _v
                    in v.items()
                    if (
                        _k.removesuffix('_').lower().endswith('id')
                        or not _k.startswith('_')
                        )
                    and (
                        _v is not None
                        if not include_null
                        else True
                        )
                    }
            elif isinstance(v, list) and not isinstance(v, str):
                dbo[k] = [
                    _v._to_dbo(camel_case, include_null)
                    if isinstance(_v, DocObject)
                    else
                    _v
                    for _v
                    in v
                    if (
                        _v is not None
                        if not include_null
                        else True
                        )
                    ]
            else:
                dbo[k] = v
        if camel_case:
            dbo = {
                utils.to_camel_case(k.strip('_')): v
                for k, v
                in dbo.items()
                }
        else:
            dbo = {
                k.removesuffix('_'): v
                for k, v
                in dbo.items()
                }
        return dbo

    @property
    def as_dbo(self) -> typing.Union[dict, list[dict]]:
        """Recursively return object as a dictionary or list thereof."""

        return self._to_dbo()

    @property
    def as_json(self) -> str:
        """Return object as a camelCase, JSON serialized string."""

        return json.dumps(self.as_rest, default=str, sort_keys=True)

    @property
    def as_rest(self) -> dict:
        """Return object as_dbo in camelCase."""

        return self._to_dbo(camel_case=True)

    @classmethod
    def from_rest(
        cls,
        rest_obj: typing.Union[str, dict[str, typing.Any]]
        ) -> 'DocObject':
        """Load object from a camelCase REST request."""

        if isinstance(rest_obj, str):
            rest_obj = json.loads(
                re.sub(
                    Constants.RE_JSON,
                    '',
                    rest_obj
                    )
                )

        return cls.from_dict(rest_obj)

    @classmethod
    def from_dict(cls, d: dict[str, typing.Any]) -> 'DocObject':
        """Instantiate object from a dict representation."""

        return cls(
            **{
                k: v
                for _k, v
                in d.items()
                if (k := cls.key_for(_k))
                }
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def enumerations(cls) -> dict[str, list]:
        """Dictionary containing all enums for object."""

        d: dict[str, list] = {}
        for k, field in cls.fields.items():
            if (
                (field_enum := field.metadata.get('enum'))
                and isinstance(field_enum, enum.EnumMeta)
                ):
                d[k] = [e.value for e in field_enum]
            elif field_enum:
                d[k] = list(field_enum)
            if d.get(k) and field.metadata.get('nullable', True):
                d[k].append(None)

        return d

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def reference(cls) -> str:
        """Unique reference to the object's name and path."""

        return Constants.DOC_DELIM.join(
            (
                *[
                    utils.to_camel_case(s)
                    for s
                    in cls.path.split('.')
                    ],
                utils.to_camel_case(cls.__name__)
                )
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def distribution(cls) -> str:
        """
        The docent distribution to which the object belongs, or,
        if the object is a member of another package, the name
        of that package.
        """

        if 'docent' in cls.path and '.objects' in cls.path:
            pkg, dist, *_ = cls.path.split('.')
            dist = dist.replace('_', '-')
            return f'{pkg}[{dist}]'
        else:
            return cls.path.split('.')[0]

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def path(cls) -> str:
        """Full path to object file within its package."""

        return cls.__module__

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def description(cls) -> str:
        """
        Brief description of the object.

        Defaults to the docstring for any derived class,
        otherwise a one-sentence description of the object's
        name and membership is generated.
        """

        default_dataclasses_docstring = cls.__name__ + '(*args, **kwargs)'
        if cls.__doc__ and cls.__doc__ != default_dataclasses_docstring:
            return cls.__doc__
        else:
            return cls.default_description

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def default_description(cls) -> str:
        """Simple description derived from class and package name."""

        return ' '.join(
            (
                'An object called',
                cls.__name__,
                'belonging to the',
                cls.distribution,
                'distribution.'
                )
            )

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def is_snake_case(cls) -> bool:
        """True if object is snake_case."""

        return utils.is_snake_case(cls.fields)

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def isCamelCase(cls) -> bool:
        """
        True if object is camelCase.

        Fields that end with 'id' (case insensitive)
        will not be evaluated.
        """

        return utils.isCamelCase(cls.fields)

    @classmethod
    @property
    def fields(cls) -> dict[str, dataclasses.Field]:
        """Return public fields for object."""

        d = {}
        v: dataclasses.Field
        for k, v in cls.__dataclass_fields__.items():
            if (
                k.startswith('_')
                and not k.removesuffix('_').lower().endswith('id')
                ):
                continue
            d[k] = v
        return d


@dataclasses.dataclass
class DocRecords(abc.ABC, DocObject):
    """
    Base docent Container Object.

    ---

    Special Method Usage
    --------------------

    ```py
    if DocRecords:
    ```

    DocRecords truthiness will evaluate to True if records \
    is not an empty list.

    ```py
    DocRecords1 + DocRecords2
    ```

    Extends records contained in DocRecords1 with all records \
    from DocRecords2.

    ```py
    DocRecords1 += DocRecords2
    ```

    In-place extension of DocRecords1 to include all records \
    from DocRecords2.

    ```py
    DocRecords1 - DocRecords2
    ```

    Removed all records contained in DocRecords1 that already \
    exist in DocRecords2.

    ```py
    DocRecords1 -= DocRecords2
    ```

    In-place removal of all records contained in DocRecords1 that already \
    exist in DocRecords2.

    """

    records: list[DocObject] = dataclasses.field(
        default_factory=list
        )

    @abc.abstractmethod
    def __iter__(self) -> typing.Iterator:
        ...

    @abc.abstractmethod
    def __getitem__(self):
        ...

    def __add__(self, other: 'DocRecords') -> 'DocRecords':
        return DocRecords(records=self.records + other.records)

    def __bool__(self) -> bool:
        return bool(self.records)

    def __iadd__(self, other: 'DocRecords') -> 'DocRecords':
        self.records.extend(other.records)
        return self

    def __isub__(self, other: 'DocRecords') -> 'DocRecords':
        self.records = [
            record
            for record
            in self.records
            if record not in other.records
            ]
        return self

    def __len__(self) -> int:
        return len(self.records)

    def __sub__(self, other: 'DocRecords') -> 'DocRecords':
        return DocRecords(
            records=[
                record
                for record
                in self.records
                if record not in other.records
                ]
            )

    @functools.cached_property
    def record_type(self) -> DocObject:  # noqa
        records_field: dataclasses.Field = self.fields['records']
        return records_field.type.__args__[0]
