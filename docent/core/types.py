__all__ = (
    'DocMeta',
    )

import abc
import functools

from . import objects


class DocMeta(abc.ABCMeta, type):  # noqa

    @classmethod
    @property
    @functools.lru_cache(maxsize=1)
    def APPLICATION_OBJECTS(cls) -> dict[str, 'objects.DocObject']:  # noqa
        return {}

    def __call__(cls, *args, **kwargs):  # noqa
        if (
            not cls.__module__.startswith('docent.core')
            and not cls.__module__.startswith('docent.rest')
            ):
            cls.APPLICATION_OBJECTS.setdefault(cls.reference, cls)
        return super().__call__(*args, **kwargs)
