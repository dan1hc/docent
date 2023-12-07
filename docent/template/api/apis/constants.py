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
    DEFAULT_RESPONSE_HEADERS: docent.rest.objects.response.Headers = (
        docent.rest.objects.response.Headers.from_list(
            [
                docent.rest.objects.response.Header(
                    header.value,
                    description=(
                        docent.rest.enums.header.DefaultHeaderValues[
                            header.name
                            ].value
                        )
                    )
                for header
                in docent.rest.enums.header.DefaultHeaders
                ]
            )
        )
