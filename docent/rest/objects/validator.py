__all__ = (
    'SchemaValidator',
    'SchemaValidationField',
    )

import dataclasses
import datetime
import enum
import re
import typing

import docent.core

from .. import exceptions

from . import base
from . import constants


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class SchemaValidationField(base.Component):  # noqa

    name: str = None
    dtype: typing.Type = None
    default: typing.Union[typing.Any, typing.Callable] = None
    enum: list[typing.Any] = dataclasses.field(default_factory=list)

    ignorance: bool = False
    nullable: bool = True
    required: bool = False
    strict_enum: bool = False

    max_length: int = None
    min_length: int = None
    pattern: str = None

    @property
    def component_type(self) -> str:  # noqa
        return None


@dataclasses.dataclass
class SchemaValidator(base.Component):  # noqa

    schema: list[SchemaValidationField] = dataclasses.field(
        default_factory=list
        )
    request_attribute: str = None
    reference_object: docent.core.objects.DocObject = None

    @property
    def component_type(self) -> str:  # noqa
        return None

    def __bool__(self) -> bool:  # noqa
        return bool(self.schema)

    def __post_init__(self):  # noqa
        self.schema = [
            SchemaValidationField(**f)
            if isinstance(f, dict)
            else f
            for f
            in self.schema
            ]

    def _validate(self, obj: dict):  # noqa
        for field in self.schema:
            if field.ignorance:
                continue
            elif (
                field.required
                and field.name not in obj
                ):
                raise SyntaxError(
                    f'Invalid request {self.request_attribute}. Missing field: {field.name}'  # noqa
                    )
            elif (value := obj.get(field.name)):
                try:
                    if field.dtype is datetime.datetime:
                        value = docent.core.utils.parse_dt(value)
                    elif isinstance(
                        field.dtype,
                        (
                            docent.core.objects.DocObject,
                            docent.core.types.DocMeta
                            )
                        ):
                        value = field.dtype.from_rest(value)
                    elif value:
                        value = field.dtype(value)
                except:
                    raise SyntaxError(
                        ' '.join(
                            (
                                f'Invalid request {self.request_attribute}. {field.name}:',  # noqa
                                f"'{value!s}' is not of type: {field.dtype!s}"
                                )
                            )
                        )
            elif field.name in obj and not field.nullable:
                raise SyntaxError(
                    ' '.join(
                        (
                            f'Invalid request {self.request_attribute}. {field.name}:',  # noqa
                            'Null value is not allowed for this field.'
                            )
                        )
                    )
            if (
                field.enum
                and field.strict_enum
                and value
                and value not in field.enum
                ):
                raise SyntaxError(
                    ' '.join(
                        (
                            f'Invalid request {self.request_attribute}.',
                            f'Value for field {field.name} must be one of:',
                            str(field.enum)
                            )
                        )
                    )
            if value and isinstance(value, str):
                if field.min_length and len(value) < field.min_length:
                    raise SyntaxError(
                        ' '.join(
                            (
                                f'Invalid request {self.request_attribute}.',
                                f"{field.name}: '{value}'",
                                f'(len: {len(value)}) must be at least',
                                str(field.min_length),
                                'characters or longer.'
                                )
                            )
                        )
                if field.max_length and len(value) > field.max_length:
                    raise SyntaxError(
                        ' '.join(
                            (
                                f'Invalid request {self.request_attribute}.',
                                f"{field.name}: '{value}'",
                                f'(len: {len(value)}) must be no more than',
                                str(field.max_length),
                                'characters in length.'
                                )
                            )
                        )
                if field.pattern and not re.match(field.pattern, value):
                    raise SyntaxError(
                        ' '.join(
                            (
                                f'Invalid request {self.request_attribute}.',
                                f"{field.name}: '{value}' must match the following regex:",
                                field.pattern
                                )
                            )
                        )

    def validate_request_attribute(
        self,
        attribute_values: typing.Union[dict, list]
        ):  # noqa
        if isinstance(attribute_values, dict):
            return self._validate(attribute_values)
        elif isinstance(attribute_values, list):
            for obj in attribute_values:
                self._validate(obj)

    def parse_dtypes(
        self,
        obj: typing.Union[dict, list]
        ) -> typing.Union[dict, list]:  # noqa
        if isinstance(obj, dict):
            return_obj = {}
            for field in self.schema:
                if field.ignorance:
                    continue
                elif (value := obj.get(field.name)):
                    name = field._name.split(Constants.FIELD_DELIM)[-1]
                    if field.dtype is datetime.datetime:
                        return_obj[name] = docent.core.utils.parse_dt(value)
                    elif isinstance(
                        field.dtype,
                        (
                            docent.core.objects.DocObject,
                            docent.core.types.DocMeta
                            )
                        ):
                        return_obj[name] = field.dtype.from_rest(value)
                    else:
                        return_obj[name] = field.dtype(value)
            return return_obj
        elif isinstance(obj, list):
            objs = []
            for o in obj:
                objs.append(self.parse_dtypes(o))
            return objs
        else:
            return obj

    @classmethod
    def from_object(
        cls,
        obj: docent.core.objects.DocObject,
        path_ids: list[str] = None,
        request_attribute: str = None,
        method_name: str = None,
        many: bool = False,
        resource_id: str = None,
        ) -> 'SchemaValidator':  # noqa

        schema: list[SchemaValidationField] = []

        for field_name, field_meta in obj.fields.items():

            if isinstance(
                field_meta.default_factory,
                dataclasses._MISSING_TYPE
                ):
                default_value = field_meta.default
            else:
                default_value = field_meta.default_factory()

            if (
                (field_enum := field_meta.metadata.get('enum', []))
                and isinstance(field_enum, enum.EnumMeta)
                ):
                field_enum = sorted(e.value for e in field_enum)

            irrelevant = (
                method_name
                and (
                    (
                        ignorance := field_meta.metadata.get(
                            'ignore',
                            (
                                {
                                    'post',
                                    'put',
                                    }
                                if request_attribute == 'parameters'
                                else
                                {
                                    'delete',
                                    'get',
                                    'patch',
                                    }
                                )
                            )
                        ) is True
                    or (
                        hasattr(ignorance, '__iter__')
                        and method_name in ignorance
                        )
                    )
                )

            requisite = (
                method_name
                and (
                    (
                        required := field_meta.metadata.get(
                            'required',
                            {}
                            )
                        ) is True
                    or (
                        hasattr(required, '__iter__')
                        and method_name in required
                        )
                    )
                and (
                    (
                        request_attribute == 'body'
                        and method_name in {'post', 'put'}
                        )
                    or (
                        request_attribute == 'parameters'
                        and method_name in {'delete', 'get', 'patch'}
                        )
                    )
                )

            if irrelevant and requisite:
                raise exceptions.ValidationConflictError(
                    '\n'.join(
                        (
                            'A field cannot be both ignored and required.\n',
                            ' :: '.join(
                                (
                                    f'METHOD - {method_name.upper()}',
                                    f"FIELD - '{field_name}'",
                                    f'IN - {request_attribute}',
                                    )
                                )
                            )
                        )
                    )

            nullability = (
                method_name
                and (
                    (
                        (
                            nullable := field_meta.metadata.get(
                                'nullable',
                                True
                                )
                            ) is True
                        or (
                            hasattr(nullable, '__iter__')
                            and method_name in nullable
                            )
                        )
                    or (
                        ignorance
                        or (
                            hasattr(ignorance, '__iter__')
                            and method_name in ignorance
                            )
                        )
                    )
                )

            if (
                (
                    many
                    and (
                        field_name != resource_id
                        or method_name.lower() == 'put'
                        )
                    )
                or not many
                ):
                schema.append(
                    SchemaValidationField(
                        _name=Constants.FIELD_DELIM.join(
                            (
                                obj.reference,
                                'validation',
                                docent.core.utils.to_camel_case(field_name.strip('_'))  # noqa
                                )
                            ),
                        name=docent.core.utils.to_camel_case(field_name.strip('_')),  # noqa
                        default=default_value,
                        dtype=field_meta.type,
                        enum=field_enum,
                        strict_enum=field_meta.metadata.get('strictEnum', False),
                        ignorance=irrelevant,
                        nullable=nullability,
                        required=requisite,
                        pattern=field_meta.metadata.get('pattern'),
                        max_length=field_meta.metadata.get('maxLength'),
                        min_length=field_meta.metadata.get('minLength'),
                        )
                    )

        for path_id in (path_ids or []):
            if (
                (
                    many
                    and (
                        path_id != resource_id
                        or method_name.lower() == 'put'
                        )
                    )
                or not many
                ) and path_id not in {field.name for field in schema}:
                schema.append(
                    SchemaValidationField(
                        _name=Constants.FIELD_DELIM.join(
                            (
                                obj.reference,
                                'validation',
                                path_id
                                )
                            ),
                        name=path_id,
                        dtype=str,
                        ignorance=False,
                        nullable=False,
                        required=True
                        )
                    )

        return cls(
            schema=schema,
            request_attribute=request_attribute,
            reference_object=obj,
            )
