__all__ = (
    'IncorrectCasingError',
    'InvalidLogMessageTypeError',
    'MissingDefaultValueError',
    'MissingContainerTypeAnnotation',
    )

from . import constants


class Constants(constants.PackageConstants):  # noqa

    pass



class IncorrectCasingError(SyntaxError):  # noqa

    pass


class InvalidLogMessageTypeError(SyntaxError):  # noqa

    pass


class MissingContainerTypeAnnotation(SyntaxError):  # noqa

    pass


class MissingDefaultValueError(SyntaxError):  # noqa

    pass
