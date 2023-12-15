import docent.rest

from .. import core


class ApiConstants(core.constants.PackageConstants):
    """Constants specific to all APIs."""

    DEFAULT_PREFICES = [
        'api',
        ]
    DEFAULT_REQUEST_HEADERS: docent.rest.objects.parameter.Parameters = (
        docent.rest.objects.parameter.Parameters.from_list(
            [
                docent.rest.objects.parameter.Header(
                    name='x-docent-template-user',
                    ),
                ]
            )
        )
