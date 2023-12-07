__all__ = (
    'In',
    )

import enum


class In(enum.Enum):  # noqa

    header        = 'header'
    path          = 'path'
    query         = 'query'
