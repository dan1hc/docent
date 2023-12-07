__all__ = (
    'Path',
    )

import re
import typing

from .. import enums

from . import base
from . import constants
from . import method
from . import parameter
from . import schema


class Constants(constants.ComponentConstants):  # noqa

    pass


class Path(base.Component):  # noqa

    delete: method.Method = None
    get: method.Method = None
    options: method.Method = None
    patch: method.Method = None
    post: method.Method = None
    put: method.Method = None

    _path_parameters: parameter.Parameters = None

    def __bool__(self) -> bool:
        return any(
            (
                self.delete is not None,
                self.get is not None,
                self.patch is not None,
                self.post is not None,
                self.put is not None,
                )
            )

    def __post_init__(self):  # noqa
        super().__post_init__()
        self._path_parameters = parameter.Parameters(
            _extensions=[
                parameter.Parameter(
                    name=path_parameter,
                    _name=Constants.FIELD_DELIM.join(
                        (
                            enums.parameter.In.path.value,
                            path_parameter
                            )
                        ),
                    in_=enums.parameter.In.path.value,
                    schema=schema.SchemaComponent(
                        _name=path_parameter,
                        type=enums.component.DataType.string.value,
                        ).as_reference,
                    required=True
                    )
                for path_parameter
                in re.findall(
                    Constants.PATH_ID_GROUP_EXPR,
                    self._name
                    )
                ]
            )

    def validate_method(
        self,
        method: str,
        request_path: str
        ):  # noqa
        if not getattr(self, method.lower()):
            raise ModuleNotFoundError(
                ' '.join(
                    (
                        f'Request method {method.upper()}',
                        'not available for resource at path:',
                        f'{request_path!s}'
                        )
                    )
                )

    @property
    def component_type(self):  # noqa
        return None

    @property
    def as_component(self) -> dict[str, dict[str, typing.Any]]:  # noqa
        d = {}
        for k, v in self.__dict__.items():
            if v is not None and not k.startswith('_'):
                v: base.Component
                d.update(v.as_reference)
        for component in self._extensions:
            d.update(component.as_reference)
        return {self._name: d}
