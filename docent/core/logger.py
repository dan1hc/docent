__all__ = (
    'get_central_log',
    )

import functools
import json
import logging
import sys
import time
import traceback
import typing
import warnings

from . import constants
from . import exceptions
from . import objects
from . import utils


class Constants(constants.PackageConstants):  # noqa

    SILENCE_MSG = 'Call to print() silenced by docent.'
    WARN_MSG    = 'Calls to print() will be silenced by docent.'


@functools.lru_cache(maxsize=1)
def get_central_log() -> logging.Logger:
    """
    Core docent logger.

    Usage
    -----

    The expectation is this will be the only log used across \
    an application.

    * Cached function that will always return the same, \
    centralized logger, formatting it on the first call.

    * Set logging level through the `LOG_LEVEL` environment variable.
        \
        * Defaults to 'DEBUG' if `Constants.ENV` is either `local` (default) \
        or `dev`, otherwise 'INFO'.

    Special Rules
    -------------

    * Can only log `str`, `dict`, and `DocObject` types.

    * Automatically redacts almost all sensitive data, including \
    api keys, tokens, credit card numbers, connection strings, \
    secrets; essentially, almost all credentials will be redacted.

    * All `warnings` will be filtered through this log and \
    displayed only once.

    * All `print` statements will be silenced *except* when \
    `Constants.ENV` is set to 'local' (its default if `ENV` \
    is unavailable in `os.environ` at runtime).
        \
        * Best practice is to set log level to 'DEBUG' and \
        use the `log.debug` method in place of `print` statements.
        \
        * `warnings` will be displayed once for all `print` \
        statements that would otherwise be silenced in any \
        non-local development environment.

    """

    logging.Formatter.converter = time.gmtime
    logging.Formatter.default_time_format = Constants.FTIME_LOG
    logging.Formatter.default_msec_format = Constants.FTIME_LOG_MSEC
    logging.basicConfig(
        format=(' ' * Constants.INDENT).join(
            (
                '{\n',
                '"level": %(levelname)s,\n',
                '"time": %(asctime)s,\n',
                '"log": %(name)s,\n',
                '"data": %(message)s}',
                )
            ),
        )

    log = logging.getLogger(__name__)
    log.setLevel(logging._nameToLevel[Constants.LOG_LEVEL])

    warnings.simplefilter('once')
    logging.captureWarnings(True)
    logging.Logger.manager.loggerDict['py.warnings'] = log

    _print = __builtins__['print']

    def _reprint(*args, **kwargs):
        if Constants.ENV == 'local':
            warnings.warn(Constants.WARN_MSG)
            _print(*args, **kwargs)
        else:
            warnings.warn(
                '\n' + '\n'.join(
                    (
                        Constants.SILENCE_MSG,
                        *[str(a) for a in args],
                        )
                    )
                )

    __builtins__['print'] = _reprint

    def _custom_log(
        level: int,
        msg: typing.Any,
        args: list,
        exc_info: bool = True,
        extra: dict = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs
        ):  # noqa
        sinfo = None
        if logging._srcfile:
            try:
                fn, lno, func, sinfo = log.findCaller(stack_info, stacklevel)
            except ValueError:
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"

        if isinstance(msg, str):
            if level == logging.WARNING:
                m = Constants.NEW_LINE_TOKEN.join(
                    spl[1:-1]
                    if (
                        '.py:' in (spl := msg.splitlines())[0]
                        and len(spl) > 2
                        )
                    else spl[:-1]
                    )
                if (
                    (spl := m.split(Constants.NEW_LINE_TOKEN))[0]
                    == Constants.SILENCE_MSG
                    ):
                    msg = {
                        'message': utils.prefix_value_to_string(spl[0]),
                        'printed': utils.prefix_value_to_string(
                            Constants.NEW_LINE_TOKEN.join(spl[1:])
                            )
                        }
                elif Constants.WARN_MSG in spl[0]:
                    msg = {'message': Constants.WARN_MSG}
                else:
                    msg = {'message': utils.prefix_value_to_string(m)}
            else:
                msg = {'message': utils.prefix_value_to_string(msg)}
        elif isinstance(msg, objects.DocObject):
            msg = {msg.__name__: msg}
        elif not isinstance(msg, dict):
            raise exceptions.InvalidLogMessageTypeError(
                'docent can only log: `dict, str, DocObject` types.'
                )

        if isinstance(exc_info, BaseException):
            exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
        elif not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
        if (
            exc_info[-1] is not None
            and not isinstance(exc_info[1], KeyboardInterrupt)
            ):
            msg['traceback'] = (
                traceback
                .format_exc()
                )

        msg: dict[str, str] = utils.convert_to_log_format(
            {
                k: (
                    [
                        (
                            _v.as_dbo
                            if isinstance(_v, objects.DocObject)
                            else _v
                            )
                        for _v
                        in v
                        ]
                    if isinstance(v, list)
                    else v.as_dbo
                    if isinstance(v, objects.DocObject)
                    else v
                    )
                for k, v
                in msg.items()
                }
            )

        record = log.makeRecord(
            log.name,
            level,
            fn,
            lno,
            (
                prefix := '\n' + (' ' * Constants.INDENT)
                ).join(
                    utils.redact_string(
                        json.dumps(
                            msg,
                            default=utils.prefix_value_to_string,
                            indent=Constants.INDENT,
                            sort_keys=True
                            )
                        ).split('\n')
                    ).replace(
                        Constants.NEW_LINE_TOKEN,
                        prefix
                        ) + '\n',
            tuple(),
            None,  # exc_info
            func,
            extra,
            sinfo
            )
        log.handle(record)

    log._log = _custom_log
    return log
