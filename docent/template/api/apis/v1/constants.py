from .. import constants


class V1Constants(constants.ApiConstants):
    """Constants specific to this API version's resources."""

    DEFAULT_PREFICES = [
        *constants.ApiConstants.DEFAULT_PREFICES,
        'v1',
        ]
