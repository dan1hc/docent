__all__ = (
    'Swagger',
    'SwaggerHTML',
    'SwaggerICON',
    'SwaggerJSON',
    'SwaggerYAML',
    )

import dataclasses
import string

import docent.core

from .. import static

from . import base
from . import constants


class Constants(constants.ComponentConstants):  # noqa

    pass


@dataclasses.dataclass
class SwaggerHTML(docent.core.objects.DocObject):  # noqa

    title: str = 'docent API'
    path: str = '/docs.yaml'
    html: str = static.HTML

    def __post_init__(self):  # noqa
        tpl = string.Template(self.html)
        self.html = tpl.safe_substitute(
            {
                'TITLE': self.title,
                'PATH': self.path
                }
            )


@dataclasses.dataclass
class SwaggerICON(docent.core.objects.DocObject):  # noqa

    img: bytes = static.ICON


@dataclasses.dataclass
class SwaggerJSON(docent.core.objects.DocObject):  # noqa

    data: str = None


@dataclasses.dataclass
class SwaggerYAML(docent.core.objects.DocObject):  # noqa

    data: str = None

    def __post_init__(self):
        yaml = ''

        for k in (
            standard_keys := (
                'openapi',
                'info',
                'servers',
                'paths',
                'components',
                )
            ):
            yaml += docent.core.utils.to_yaml({k: self.data[k]})

        for k in sorted(self.data):
            if k not in standard_keys:
                yaml += docent.core.utils.to_yaml({k: self.data[k]})

        self.data = yaml


class Swagger(metaclass=base.ComponentMeta):  # noqa

    PATH_PREFICES: list[str] = []
    PATH_SUFFICES: list[str] = []
