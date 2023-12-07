__all__ = (
    'SchemaArray',
    'SchemaObject',
    'SchemaProperty',
    'SchemaComponent',
    )

import dataclasses
import enum
import typing

import docent.core

from .. import enums

from . import base
from . import constants


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class SchemaComponent(base.Component):  # noqa

    type: str = dataclasses.field(
        default=None,
        metadata={
            'enum': sorted(
                e.value
                for e
                in enums.component.DataType
                ),
            'required': False
            }
        )
    format: str = dataclasses.field(
        default=None,
        metadata={
            'enum': sorted(
                e.value
                for e
                in enums.component.TypeFormat
                ),
            'required': False
            }
        )
    enum: list[typing.Any] = None
    nullable: bool = None
    default: typing.Any = None

    @property
    def component_type(self) -> str:  # noqa
        return enums.component.ComponentType.schemas.value

    @staticmethod
    def from_py_type(
        dtype: typing.Type,
        name: str = None,
        module: str = None,
        method_name: str = None,
        response: bool = False,
        ) -> 'SchemaComponent':  # noqa
        if isinstance(dtype, str):
            reference = Constants.DOC_DELIM.join(
                (
                    (method_name or 'base'),
                    *[
                        docent.core.utils.to_camel_case(s)
                        for s
                        in module.split('.')
                        ],
                    docent.core.utils.to_camel_case(dtype)
                    )
                )
            return {
                '$ref': '/'.join(
                    (
                        '#',
                        'components',
                        'schemas',
                        reference
                        )
                    )
                }
        elif isinstance(dtype, typing._UnionGenericAlias):
            dtypes = dtype.__args__
            _dtypes = [
                SchemaObject.from_object(t, method_name, response=response) if (  # noqa
                    isinstance(
                        t,
                        (
                            docent.core.objects.DocObject,
                            docent.core.types.DocMeta
                            )
                        )
                    ) else SchemaComponent.from_py_type(
                        t,
                        name=name,
                        module=module,
                        method_name=method_name,
                        response=response,
                        )
                for t
                in dtypes
                ]
            return SchemaProperty(
                _name=Constants.DOC_DELIM.join(
                    (
                        (method_name or 'base'),
                        name,
                        'any'
                        )
                    ) if name else None,
                anyOf=_dtypes
                )
        elif hasattr(dtype, '__args__'):
            dtypes = dtype.__args__
            _dtypes = [
                SchemaObject.from_object(t, method_name, True, response) if (
                    isinstance(
                        t,
                        (
                            docent.core.objects.DocObject,
                            docent.core.types.DocMeta
                            )
                        )
                    ) else SchemaComponent.from_py_type(
                        t,
                        name=name,
                        module=module,
                        method_name=method_name,
                        response=response,
                        )
                for t
                in dtypes
                ]
            return SchemaArray(
                _name=Constants.DOC_DELIM.join(
                    (
                        (method_name or 'base'),
                        name,
                        'many'
                        )
                    ) if name else None,
                type=enums.component.DataType.array.value,
                items=(
                    SchemaProperty(anyOf=_dtypes)
                    if len(dtypes) > 1
                    else _dtypes[0]
                    )
                )
        elif isinstance(
            dtype,
            (
                docent.core.objects.DocObject,
                docent.core.types.DocMeta
                )
            ):
            return SchemaObject.from_object(
                dtype,
                method_name=method_name,
                response=response
                )
        else:
            return SchemaComponent(
                _name=Constants.DOC_DELIM.join(
                    (
                        (method_name or 'base'),
                        name
                        )
                    ) if name else None,
                **Constants.REST_TYPES.get(
                    dtype,
                    {'type': enums.component.DataType.object.value}
                    )
                )


@dataclasses.dataclass
class SchemaProperty(SchemaComponent):  # noqa

    anyOf: list[SchemaComponent] = None


@dataclasses.dataclass
class SchemaArray(SchemaComponent):  # noqa

    items: typing.Union[SchemaProperty, SchemaComponent] = None


@dataclasses.dataclass
class SchemaObject(SchemaComponent):  # noqa

    properties: dict[str, SchemaComponent] = None
    required: list[str] = None

    @classmethod
    def from_object(
        cls,
        obj: docent.core.objects.DocObject,
        method_name: str = None,
        many: bool = False,
        response: bool = False,
        ) -> 'SchemaObject':  # noqa

        dbo: dict[str, typing.Any] = {}
        required_fields = []

        for k, field in obj.fields.items():
            if (
                method_name
                and (
                    (
                        ignorance := field.metadata.get(
                            'ignore',
                            (
                                {
                                    'post',
                                    'put',
                                    }
                                if (
                                    (
                                        is_id_field := (
                                            k
                                            .lower()
                                            .strip('_')
                                            .endswith('id')
                                            )
                                        )
                                    and not many
                                    and not response
                                    )
                                else {
                                    'post',
                                    }
                                if (
                                    is_id_field
                                    and many
                                    and not response
                                    )
                                else {}
                                )
                            )
                        ) is True
                    or (
                        hasattr(ignorance, '__iter__')
                        and method_name in ignorance
                        )
                    )
                ):
                continue

            schema = SchemaComponent.from_py_type(
                field.type,
                name=Constants.FIELD_DELIM.join(
                    (
                        obj.reference,
                        k
                        )
                    ),
                module=obj.__module__,
                method_name=method_name,
                response=response
                )

            if (
                method_name
                and (
                    (
                        required := field.metadata.get('required', {})
                        ) is True
                    or (
                        hasattr(required, '__iter__')
                        and method_name in required
                        )
                    )
                ):
                required_fields.append(
                    docent.core.utils.to_camel_case(
                        k.strip('_')
                        )
                    )
            elif (default_value := field.default) is None:
                schema.nullable = True
                schema.default = default_value
            elif not isinstance(default_value, dataclasses._MISSING_TYPE):
                schema.default = default_value
            elif isinstance(
                (default_value := field.default_factory()),
                docent.core.objects.DocObject
                ):
                schema.default = default_value.as_rest
            else:
                schema.default = default_value

            if (
                field_enum := field.metadata.get(
                    'enum',
                    []
                    )
                ):
                if isinstance(field_enum, enum.EnumMeta):
                    field_enum = sorted(e.value for e in field_enum)
                if (
                    schema.nullable
                    and (not method_name or not required)
                    ):
                    if None not in field_enum:
                        field_enum.append(None)
                schema.enum = field_enum

            if (instance_value := getattr(obj, k)) != schema.default:
                schema.default = instance_value

            dbo[k] = schema

        spec = cls(
            _name=Constants.DOC_DELIM.join(
                (
                    (method_name or 'base'),
                    'many' if many else 'one',
                    obj.reference
                    )
                ),
            properties={
                docent.core.utils.to_camel_case(k.strip('_')): v
                for k, v
                in dbo.items()
                },
            required=required_fields or None,
            type=enums.component.DataType.object.value
            )

        return spec
