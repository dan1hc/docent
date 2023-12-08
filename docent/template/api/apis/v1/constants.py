import docent.rest

from .. import constants


class V1Constants(constants.ApiConstants):
    """Constants specific to this API version's resources."""

    DEFAULT_PREFICES = [
        *constants.ApiConstants.DEFAULT_PREFICES,
        'v1',
        ]
    DEFAULT_AUTHORIZERS: list[docent.rest.objects.security.Authorizer] = [
        docent.rest.objects.security.Authorizer(
            name='x-docent-api-key',
            in_=docent.rest.enums.parameter.In.header.value,
            type=docent.rest.enums.security.SecurityScheme.apiKey.value,
            ),
        ]
