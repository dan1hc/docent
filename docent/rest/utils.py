__all__ = (
    'convert_open_api_spec',
    'dtype_to_schema',
    'extract_path_parameters',
    'get_schema_reference_from_object',
    'filter_component_name',
    'filter_component_uri',
    'sort_on_last_field',
    'spec_from_api',
    'to_yaml',
    )

import functools
import importlib
import os
import re
import typing

import docent.core

from . import constants
from . import enums


class Constants(constants.FrameworkConstants):  # noqa

    pass


def convert_open_api_spec(
    spec: typing.Union[dict, list],
    unsupported_keywords: set,
    ) -> dict:  # noqa
    if isinstance(spec, dict):
        d = {}
        for k, v in spec.items():
            if k in unsupported_keywords:
                continue
            elif isinstance(v, dict):
                d[k] = {
                    _k: convert_open_api_spec(
                        _v,
                        unsupported_keywords,
                        )
                    if
                    isinstance(
                        _v, 
                        (dict, list)
                        )
                    else
                    _v
                    for _k, _v
                    in v.items()
                    if _k not in unsupported_keywords
                    }
            elif isinstance(v, list):
                d[k] = [
                    convert_open_api_spec(
                        _v,
                        unsupported_keywords,
                        )
                    if
                    isinstance(
                        _v, 
                        (dict, list)
                        )
                    else
                    _v
                    for _v
                    in v
                    ]
            else:
                d[k] = v
    else:
        d = []
        for v in spec:
            if isinstance(v, dict):
                d.append(
                    {
                        _k: convert_open_api_spec(
                            _v,
                            unsupported_keywords,
                            )
                        if
                        isinstance(
                            _v, 
                            (dict, list)
                            )
                        else
                        _v
                        for _k, _v
                        in v.items()
                        if _k not in unsupported_keywords
                        }
                    )
            elif isinstance(v, list):
                d.append(
                    [
                        convert_open_api_spec(
                            _v,
                            unsupported_keywords,
                            )
                        if
                        isinstance(
                            _v, 
                            (dict, list)
                            )
                        else
                        _v
                        for _v
                        in v
                        ]
                    )
            else:
                d.append(v)
    return d


@functools.cache
def get_schema_reference_from_object(
    obj: docent.core.objects.DocObject
    ) -> dict[str, dict]:
    """Get OpenAPI schema $ref from DocObject."""

    return {'$ref': obj.reference}


def dtype_to_schema(dtype: typing.Type) -> dict:  # noqa
    if isinstance(dtype, typing._UnionGenericAlias):
        dtypes = dtype.__args__
        return {
            'anyOf': [
                dtype_to_schema(t)
                for t
                in dtypes
                ]
            }
    elif hasattr(dtype, '__args__'):
        dtypes = dtype.__args__
        _dtypes = [
            dtype_to_schema(t)
            for t
            in dtypes
            ]
        return {
            'type': enums.component.DataType.array.value,
            'items': {'anyOf': _dtypes} if len(dtypes) > 1 else _dtypes[0]
            }
    elif isinstance(
        dtype,
        (
            docent.core.objects.DocObject,
            docent.core.types.DocMeta
            )
        ):
        return get_schema_reference_from_object(dtype.reference)
    else:
        return Constants.REST_TYPES.get(
            dtype,
            {'type': enums.component.DataType.object.value}
            )


def filter_component_name(ref: str) -> str:  # noqa
    ref = re.sub(
        r'([{}])',
        '',
        ref
        )
    ref = re.sub(
        r'([\/:])',
        Constants.DOC_DELIM,
        ref
        )
    return ref


def filter_component_uri(ref: str) -> str:  # noqa
    ref_tag, component_tag, component_type, *ref = ref.split('/')
    ref = re.sub(
        r'([{}])',
        '',
        '/'.join(ref)
        )
    ref = re.sub(
        r'([\/:])',
        Constants.DOC_DELIM,
        ref
        )
    return '/'.join((ref_tag, component_tag, component_type, ref))


@functools.lru_cache(maxsize=1)
def spec_from_api(
    args: tuple[str],
    help_text: str,
    valid_flags: tuple[str],
    valid_kwarg_flags: tuple[str],
    default_openapi_version: str,
    default_app_version: str,
    ) -> dict:  # noqa

    if '--help' in args:
        docent.core.log.info(help_text)
        return

    if len(args) < 2:
        raise SyntaxError(
            "Please specify an importable 'python_package' for conversion.",
            )

    for a in args[2:]:
        if a.split('=')[0] not in valid_flags:
            raise SyntaxError(f'Invalid flag: {a!s}')

    for a in args[2:]:
        if (
            (a.split('=')[0] in valid_kwarg_flags)
            and not '=' in a
            ):
            raise SyntaxError(
                ' '.join(
                    (
                        f'Invalid flag: {a!s}.',
                        'Must specify target value using --flag={value}'
                        )
                    )
                )

    api_module = importlib.import_module(args[1])

    from . import objects
    from . import api

    include_url_base = '--include-base-path' in args

    if (
        openapi_version_args := [
            a
            for a
            in args if a.startswith('--openapi-version')
            ]
        ) and (openapi_version_arg := openapi_version_args[0]):
        openapi_version = openapi_version_arg.split('=')[-1]
    else:
        openapi_version = default_openapi_version

    if (
        app_title_args := [
            a
            for a
            in args if a.startswith('--title')
            ]
        ) and (app_title_arg := app_title_args[0]):
        app_title = app_title_arg.split('=')[-1]
    else:
        app_title = docent.core.utils.to_camel_case(api_module.__name__)

    if (
        app_version_args := [
            a
            for a
            in args if a.startswith('--version')
            ]
        ) and (app_version_arg := app_version_args[0]):
        app_version = app_version_arg.split('=')[-1]
    else:
        app_version = getattr(api_module, '__version__') if hasattr(
            api_module,
            '__version__'
            ) else default_app_version

    if (
        url_root_args := [
            a
            for a
            in args if a.startswith('--url')
            ]
        ) and (url_root_arg := url_root_args[0]):
        url_root = url_root_arg.split('=')[-1]
    else:
        url_root = os.getenv('HOSTNAME', '/')

    server_variables = {}
    if include_url_base:
        url_root += '/{basePath}'

    info = {
        'title': app_title,
        'description': '\n'.join(
            (
                '---',
                '\n',
                ' - '.join(
                    (
                        '__API created with [docent](https://docent.1howardcapital.com/docent)__',
                        f'_v{docent.core.__version__}_',
                        )
                    ),
                '\n',
                '---',
                (api_module.__doc__ or '')
                )
            ),
        'version': f'v{app_version}',
        }

    server = {'url': url_root}
    if server_variables:
        server['variables'] = server_variables

    servers = [server]

    tags: list[dict] = []
    _paths: dict[str, dict] = {}
    _verbose = '--verbose' in args or '-v' in args
    for (*_, resource) in api.APIMeta.APPLICATION_RESOURCES:
        if _verbose:
            docent.core.log.info(f'PARSING RESOURCE :: {resource.__name__}')
        for path in resource.PATHS[resource.resource_key].values():  # noqa
            if path:
                if _verbose:
                    docent.core.log.info(path._name)
                _paths.update(path.as_component)
        desc = (
            (
                doc_lines := (
                    (
                        resource.__doc__
                        if (
                            resource.__doc__
                            != resource.__name__ + '(*args, **kwargs)'
                            )
                        else None
                        )
                    or (
                        resource.resource.__doc__
                        if (
                            resource.resource.__doc__
                            != (
                                resource.resource.__name__
                                + '(*args, **kwargs)'
                                )
                            )
                        else None
                        )
                    or resource.resource.default_description
                    ).strip().splitlines()
                )[0]
            )
        if len(doc_lines) > 1:
            desc += '\n' + '\n'.join(
                (
                    '<details>',
                    '',
                    'Details',
                    '=======',
                    *[
                        l.strip()
                        for l
                        in doc_lines[1:]
                        ],
                    '',
                    '</details>'
                    )
                )
        if (n := resource.tags[-1]) != 'healthz':
            tags.append(
                {
                    'name': n,
                    'description': desc,
                    }
                )

    tags.append(
        {
            'name': 'healthz',
            'description': '\n'.join(
                (
                    'Standard application health monitoring endpoint.',
                    "Requests made to '/' route here as well.",
                    )
                ),
            }
        )

    paths: dict[str, dict] = {}
    for k in _paths:
        v = _paths[k]
        if not k.startswith('/'):
            k = '/' + k
        paths[k] = v

    components = {}

    for component_type, app_components in (
        objects.ComponentMeta.APPLICATION_COMPONENTS.items()
        ):
        d = {}
        for component in app_components.values():
            d.update(component.as_component)
        d = {filter_component_name(ref): v for ref, v in d.items()}
        components[component_type] = d

    spec = {
        'openapi': openapi_version,
        'info': info,
        'servers': servers,
        'paths': paths,
        'components': components,
        'tags': tags,
        }

    return convert_open_api_spec(
        spec,
        {
            'options',
            }
        )


def sort_on_last_field(k: typing.Union[str, dict]) -> str:  # noqa
    if isinstance(k, dict):
        k = k.get('$ref')
    if not k:
        return 'Z'
    elif isinstance(k, str):
        return k.split(
            Constants.DOC_DELIM
            )[-1].split(Constants.FIELD_DELIM)[-1]
    else:
        return str(k)


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
                if v:
                    yaml += (' ' * (indent + 2))
            yaml += to_yaml(v, indent + 2)
    elif isinstance(e, list):
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
    elif isinstance(e, str) and '\n' in e:
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
