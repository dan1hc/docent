__all__ = (
    'camel_case_to_kebab_case',
    'camel_case_to_snake_case',
    'convert_to_log_format',
    'isCamelCase',
    'is_snake_case',
    'parse_dt',
    'prefix_value_to_string',
    'redact_log_dict',
    'redact_string',
    'to_camel_case',
    'to_yaml',
    'snake_case_to_kebab_case',
    )

import datetime
import re
import typing

from . import constants
from . import patterns


class Constants(constants.PackageConstants):  # noqa

    REDACT_DICT_KEY_PATTERNS = [
        {
            'ID': 'api-key-token',
            'Severity': 'HIGH',
            'Title': 'API Key',
            'Regex': re.compile(r"""(?i)(api|secret)+([\S]*[\W_]+)?(key|token)"""),
            },
        {
            'ID': 'authorization-header',
            'Severity': 'HIGH',
            'Title': 'Authorization Header',
            'Regex': re.compile(r"""(?i)(authorization|bearer)+"""),
            },
        ]
    REDACT_LOG_STR_PATTERNS  = [
        {
            'ID': 'conn-string-password',
            'Severity': 'HIGH',
            'Title': 'Connection String Password',
            'Regex': re.compile(r"""(:\/\/)+\w+(:[^:@]+)@"""),
            },
        {
            'ID': 'credit-card',
            'Severity': 'HIGH',
            'Title': 'Credit Card',
            'Regex': re.compile(r"""\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b"""),
            },
        *patterns.REDACTION_PATTERNS
        ]


def redact_string(string: str) -> str:
    """Redact potentially sensitive values from being logged."""

    for r in Constants.REDACT_LOG_STR_PATTERNS:
        reason: str = r['Title']
        regex: re.Pattern = r['Regex']
        string = regex.sub(
            repl=f'[ REDACTED :: {reason.upper()} ]',
            string=string
            )

    return string


def redact_log_dict(
    obj: typing.Any,
    ) -> typing.Union[dict, typing.Any]:
    """Redact potentially sensitive values from being logged (based on dict key)."""  # noqa

    if isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                d[k] = redact_log_dict(v)
            elif isinstance(v, str):
                d[k] = v
                for r in Constants.REDACT_DICT_KEY_PATTERNS:
                    regex: re.Pattern = r['Regex']
                    if regex.search(k) is not None:
                        reason: str = r['Title']
                        d[k] = f'[ REDACTED :: {reason.upper()} ]'
                        break
            else:
                d[k] = v
    elif isinstance(obj, list):
        d = []
        for v in obj:
            if isinstance(v, (dict, list)):
                d.append(redact_log_dict(v))
            elif isinstance(v, str):
                matched = False
                for r in Constants.REDACT_DICT_KEY_PATTERNS:
                    regex: re.Pattern = r['Regex']
                    if regex.search(v) is not None:
                        reason: str = r['Title']
                        d.append(f'[ REDACTED :: {reason.upper()} ]')
                        matched = True
                        break
                if not matched:
                    d.append(v)
            else:
                d.append(v)

    return d


def parse_dt(dt_string: str) -> datetime.datetime:
    """Parse string to datetime."""

    if 'T' in dt_string:
        return datetime.datetime.fromisoformat(dt_string)
    elif ' ' in dt_string:
        return datetime.datetime.strptime(
            dt_string,
            Constants.FTIME_DEFAULT.replace('T', ' ')
            )
    elif len(dt_string.split('-')) == 3:
        return datetime.datetime.strptime(
            dt_string,
            Constants.FTIME_US_YEAR
            )


def prefix_value_to_string(v: typing.Any, extra_indentation: int = Constants.INDENT) -> str:
    """Prefix indentation to any value as a string."""

    return (
        prefix + prefix.join(
            (
                s[:Constants.LOG_CUTOFF_LEN],
                ' ... ',
                ' ... ',
                ' ... ',
                )
            )
        if len(
            s := (
                str(v)
                .rstrip('\n')
                .replace(
                    '\n',
                    (
                        prefix := Constants.NEW_LINE_TOKEN + (
                            ' ' * (Constants.INDENT + extra_indentation)
                            )
                        )
                    )
                )
            ) > Constants.LOG_CUTOFF_LEN
        else s
        )


def convert_to_log_format(
    msg: dict[str, typing.Any],
    extra_indentation: int = Constants.INDENT
    ) -> dict[str, str]:
    """Recursively convert a dict[str, typing.Any] to dict[str, str]."""

    extra_indentation += Constants.INDENT
    return {
        k: (
            [
                convert_to_log_format(_v, extra_indentation)
                if isinstance(_v, dict)
                else prefix_value_to_string(_v, extra_indentation)
                for _v
                in v
                ]
            if isinstance(v, list)
            else {
                _k: (
                    convert_to_log_format(_v, extra_indentation)
                    if isinstance(_v, dict)
                    else prefix_value_to_string(_v, extra_indentation)
                    )
                for _k, _v
                in v.items()
                }
            if isinstance(v, dict)
            else prefix_value_to_string(v, extra_indentation)
            )
        for k, v
        in redact_log_dict(msg).items()
        }


def camel_case_to_kebab_case(camel_case_str: str) -> str:
    """Convert a camelCase string to kebab-case."""

    return snake_case_to_kebab_case(
        camel_case_to_snake_case(camel_case_str)
        )


def snake_case_to_kebab_case(snake_case_str: str) -> str:
    """Convert a snake_case string to kebab-case."""

    return snake_case_str.replace('_', '-')


def camel_case_to_snake_case(camel_case_str: str) -> str:
    """Convert a camelCase string to snake_case."""

    camel_case_str = camel_case_str[0].lower() + camel_case_str[1:]
    return ''.join(
        (
            character
            if (character.islower() or not character.isalpha())
            else f'_{character}'
            for character
            in camel_case_str
            )
        ).lower()


def is_snake_case(fields: list[str]) -> bool:
    """True if all fields are snake_case."""

    return all(
        f == camel_case_to_snake_case(f)
        for _f
        in fields
        if (f := _f.strip('_'))
        )


def isCamelCase(fields: list[str]) -> bool:
    """
    True if all fields are camelCase.

    Fields that end with 'id' (case insensitive)
    will not be evaluated.
    """

    return all(
        f == to_camel_case(f)
        for _f
        in fields
        if (f := _f.strip('_'))
        and not f.lower().endswith('id')
        )


def to_camel_case(string: str) -> str:
    """Convert a snake_case or kebab-case string to camelCase."""

    string = string[0].lower() + string[1:]
    characters = []
    capitalize = False
    for i, character in enumerate(string):
        if character in {'_', '-'}:
            capitalize = True
        elif capitalize:
            capitalize = False
            characters.append(character.upper())
        elif (
            character.isupper()
            and i < len(string) - 2
            and string[i + 1].islower()
            ):
            characters.append(character)
        else:
            characters.append(character.lower())

    return ''.join(characters)


def to_yaml(e: typing.Any, indent: int = 0) -> str:
    """Convert a dictionary to a valid yaml string."""

    yaml = ''
    if isinstance(e, dict):
        for i, k in enumerate(sorted(e)):
            v = e[k]
            if i > 0:
                yaml += (' ' * indent)
            if (
                (k.isnumeric() and len(k) == 3)
                or k.startswith('{')
                ):
                k = f"'{k}'"
            yaml += f'{k}:'
            if isinstance(v, dict):
                yaml += '\n'
                yaml += (' ' * (indent + 2))
            yaml += to_yaml(v, indent + 2)
    elif not (is_string := isinstance(e, str)) and isinstance(e, list):
        if e and isinstance(e[0], dict) and '$ref' in [0]:
            sort_on = lambda x: x.get('$ref', '')
        elif e and isinstance(e[0], dict):
            sort_on = lambda x: x.get('_name', 'Z')
        else:
            sort_on = lambda x: x or 'Z'
        if e:
            yaml += '\n'
            for v in sorted(e, key=sort_on):
                yaml += (' ' * indent) + '-' + (
                    ' '
                    if
                    isinstance(v, dict)
                    else
                    ''
                    )
                yaml += to_yaml(v, indent + 2)
        else:
            yaml += ' []\n'
    elif is_string and '\n' in e:
        strings = e.split('\n')
        yaml += ' |\n'
        for s in strings:
            yaml += (' ' * (indent + 2)) + s + '\n'
    else:
        is_boolean = isinstance(e, bool)
        is_null = e is None

        _e: str = str(e)
        if '-' in _e or '/' in _e:
            is_date = (
                all(s.isnumeric() for s in _e.split('-'))
                or all(s.isnumeric() for s in _e.split('/'))
                )
        else:
            is_date = False
        is_reference = _e.startswith('#')
        is_star = e == '*'

        if is_null:
            e = 'null'
        elif is_date or is_reference or is_star:
            e = f"'{_e}'"
        elif is_boolean:
            e = _e.lower()

        yaml += f' {e!s}'
        yaml += '\n'

    return yaml
