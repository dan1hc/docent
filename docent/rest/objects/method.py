__all__ = (
    'Method',
    )

import dataclasses
import typing

import docent.core


from . import base
from . import constants
from . import parameter
from . import request
from . import response
from . import security
from . import validator


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class Method(base.Component):  # noqa

    parameters: parameter.Parameters = None
    requestBody: request.RequestBody = None
    responses: response.Responses = None
    security_: list[security.Authorizer] = None
    tags: list[str] = None
    description: str = None
    summary: str = None

    _callable: typing.Callable[
        [request.Request],
        docent.core.objects.DocObject
        ] = None
    _response_headers: response.Headers = None
    _body_validator: validator.SchemaValidator = None
    _parameters_validator: validator.SchemaValidator = None
    _many: bool = False

    def __bool__(self) -> bool:
        return self._callable is not None

    def __call__(
        self,
        request: request.Request,
        ) -> typing.Union[
            docent.core.objects.DocObject,
            list[docent.core.objects.DocObject],
            ]:  # noqa
        return self._callable(request)

    def __post_init__(self):  # noqa
        if (
            self._body_validator
            and not self._body_validator.request_attribute
            ):
            self._body_validator.request_attribute = 'body'
        if (
            self._parameters_validator
            and not self._parameters_validator.request_attribute
            ):
            self._parameters_validator.request_attribute = 'parameters'
        if not self.summary:
            method_name = self._name.upper()
            if (
                m := method_name in {
                    'DELETE',
                    'GET',
                    'PUT',
                    }
                ) and self._many:
                method_name += ' (MANY)'
            elif m:
                method_name += ' (ONE)'
            if isinstance(
                (return_type := self._callable.__annotations__['return']),
                (docent.core.DocObject, docent.core.DocMeta)
                ):
                self.summary = ' '.join(
                    (
                        method_name,
                        'method for the',
                        return_type.__name__,
                        'resource.'
                        )
                    )
            elif (
                hasattr(return_type, '__args__')
                and isinstance(
                    return_type := return_type.__args__[0],
                    (docent.core.DocObject, docent.core.DocMeta)
                    )
                ):
                self.summary = ' '.join(
                    (
                        method_name,
                        'method for the',
                        return_type.__name__,
                        'resource.'
                        )
                    )
            else:
                self.summary = ' '.join(
                    (
                        method_name,
                        'method for the specified resource.'
                        )
                    )
            if (
                'HeartBeat resource' in self.summary
                or 'Enumeration resource' in self.summary
                ):
                self.summary = self.summary.replace(' (MANY)', '')
        if self.description:
            self.description = '\n'.join(
                [
                    l.strip()
                    for l
                    in self.description.splitlines()
                    ]
                )

    def parse_request_dtypes(
        self,
        body: typing.Union[bytes, dict, list, str] = None,
        params: dict = None,
        ) -> tuple[typing.Union[bytes, dict, list, str], dict]:  # noqa
        if body and self._body_validator and isinstance(body, (dict, list)):
            body = self._body_validator.parse_dtypes(body)
        if params and self._parameters_validator:
            params = self._parameters_validator.parse_dtypes(params)
        return body, params

    def validate_against_schema(
        self,
        request_attribute: str,
        attribute_values: typing.Union[dict, list],
        ):  # noqa
        request_validator: validator.SchemaValidator
        if (
            request_validator := getattr(
                self,
                '_'.join(('', request_attribute, 'validator'))
                )
            ):
            request_validator.validate_request_attribute(attribute_values)

    @property
    def component_type(self) -> str:  # noqa
        return None

    @property
    def as_component(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = self._to_component()
        for component in self._extensions:
            d.update(component.as_reference)
        if self._name:
            return {self._name: d}
        else:
            return d
