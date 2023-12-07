__all__ = (
    'BaseRequestError',
    'InvalidReturnSignatureError',
    'MethodNotAllowedError',
    'MethodNotImplementedError',
    'NotAuthenticatedError',
    'NotAuthorizedError',
    'NotRESTfulError',
    'RequestError',
    'ReservedKeywordError',
    'ResourceLockedError',
    'ResourceNotFoundError',
    'UnexpectedError',
    'ValidationConflictError',
    )


class InvalidReturnSignatureError(SyntaxError):  # noqa

    pass


class NotRESTfulError(SyntaxError):  # noqa

    pass


class ReservedKeywordError(SyntaxError):  # noqa

    pass


class ValidationConflictError(SyntaxError):  # noqa

    pass


class BaseRequestError(Exception):
    """Base class for all request handling exceptions."""

    def __init_subclass__(cls) -> None:
        _init = cls.__init__
        def __reinit__(cls, *args):
            return _init(cls, *(args or (cls.__doc__, )))
        cls.__init__ = __reinit__
        return super().__init_subclass__()


class RequestError(BaseRequestError):
    """Operation could not be completed due to an error with the request."""


class NotAuthenticatedError(BaseRequestError):
    """Must be authenticated to complete the request."""


class NotAuthorizedError(BaseRequestError):
    """Not authorized to complete the request."""


class ResourceNotFoundError(BaseRequestError):
    """Requested resource could not be found at the specified location."""


class ResourceLockedError(BaseRequestError):
    """Requested resource is currently locked by another user."""


class MethodNotAllowedError(BaseRequestError):
    """That method is not allowed for the requested resource."""


class MethodNotImplementedError(BaseRequestError):
    """That method has not yet been implemented for the requested resource."""


class UnexpectedError(BaseRequestError):
    """An unexpected error occurred."""
