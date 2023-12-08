__all__ = (
    'convert_open_api_spec',
    'dtype_to_schema',
    'extract_path_parameters',
    'get_schema_reference_from_object',
    'filter_component_name',
    'filter_component_uri',
    'sort_on_last_field',
    'spec_from_api',
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

    api = importlib.import_module(args[1])

    from . import objects
    from . import route

    is_aws_lambda = '--aws-lambda' in args
    is_aws_api_gateway = '--aws-api-gateway' in args
    include_aws_proxy = is_aws_api_gateway and is_aws_lambda

    if is_aws_lambda or is_aws_api_gateway:
        try:
            an_aws = importlib.import_module('docent.aws')
        except ImportError as e:
            raise ImportError(
                ' '.join(
                    (
                        'AWS extension required. Install with:',
                        '$ pip install docent[aws]'
                        )
                    )
                )

    include_url_base = '--include-base-path' in args
    include_env_suffix = '--suffix-env' in args

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
        app_env_args := [
            a
            for a
            in args if a.startswith('--env')
            ]
        ) and (app_env_arg := app_env_args[0]):
        app_env = app_env_arg.split('=')[-1]
    else:
        app_env = 'dev'

    if (
        app_title_args := [
            a
            for a
            in args if a.startswith('--title')
            ]
        ) and (app_title_arg := app_title_args[0]):
        app_title = app_title_arg.split('=')[-1]
    else:
        app_title = docent.core.utils.to_camel_case(api.__name__)

    if (
        app_version_args := [
            a
            for a
            in args if a.startswith('--version')
            ]
        ) and (app_version_arg := app_version_args[0]):
        app_version = app_version_arg.split('=')[-1]
    else:
        app_version = getattr(api, '__version__') if hasattr(
            api,
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
        url_root = os.getenv('HOST', '/')

    server_variables = {}
    if include_url_base:
        url_root += '/{basePath}'

    if app_env.lower() != 'prod' and include_env_suffix:
        url_root += f'/{app_env}'

    info = {
        'title': app_title,
        'description': '\n'.join(
            (
                '---',
                '\n',
                ' - '.join(
                    (
                        '__API created with Docent__',
                        f'_v{docent.core.__version__}_',
                        )
                    ),
                '\n',
                '---',
                (api.__doc__ or '')
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
    for (*_, resource) in route.RouteMeta.APPLICATION_RESOURCES:
        if _verbose:
            docent.core.log.info(f'PARSING RESOURCE :: {resource.__name__}')
        for path in resource.PATHS['.'.join((resource.__module__, resource.__name__))].values():  # noqa
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

    if include_aws_proxy:
        _paths.update(
            an_aws.objects.lambda_function.utils.
                get_proxy_plus_template().as_component
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

    extensions = {}
    if is_aws_api_gateway:
        extensions.update(
            an_aws.objects.api_gateway.Policy().as_component
            )
        extensions.update(
            an_aws.objects.api_gateway.BinaryMediaTypes(
                media_types=[
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # noqa
                    'image/vnd.microsoft.icon',
                    'image/x-icon',
                    'image/ico',
                    'image/jpeg',
                    'image/png',
                    ]
                ).as_component
            )

    spec = {
        'openapi': openapi_version,
        'info': info,
        'servers': servers,
        'paths': paths,
        'components': components,
        'tags': tags,
        **extensions
        }

    if is_aws_api_gateway:
        spec = convert_open_api_spec(
            spec,
            {'default', 'example'}
            )

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
    return k.split(
        Constants.DOC_DELIM
        )[-1].split(Constants.FIELD_DELIM)[-1]


def extract_path_parameters(path: str) -> dict[str, str]:  # noqa

    from . import resource
    from . import route

    path_as_list = path.split('/')
    path_parameters = {}

    for resource_meta in route.RouteMeta.APPLICATION_RESOURCES:
        path_trimmed = '/'.join(
            [
                v
                for i, v
                in enumerate(path_as_list)
                if (
                    i not in resource_meta[1]
                    and i <= len(resource_meta[0].split('/'))
                    )
                ]
            )
        if resource_meta[0] == path_trimmed:
            rsc: resource.Resource = resource_meta[2]
            path_key = rsc.validate_path(path_as_list)
            path_obj = rsc.PATHS[
                '.'.join((rsc.__module__, rsc.__name__))
                ][path_key]
            path_ref_as_list = path_obj._name.split('/')
            path_parameters = {
                path_ref_as_list[i][1:-1]: v
                for i, v
                in enumerate(path_as_list)
                if (
                    i in resource_meta[1]
                    or (
                        i == len(resource_meta[0].split('/')) + 1
                        and path_key == 'ID'
                        )
                    )
                }

    return path_parameters
