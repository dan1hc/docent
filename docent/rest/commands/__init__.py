import importlib
import os
import socketserver
import sys

import docent.core

DEFAULT_OPENAPI_VERSION = '3.0.1'
DEFAULT_APP_VERSION = '0.0.1.dev1'
VALID_ARG_FLAGS = (
    '--aws-api-gateway',
    '--aws-lambda',
    '--include-base-path',
    '--suffix-env',
    '-v',
    '--verbose',
    )
VALID_KWARG_FLAGS = (
    '--env',
    '--openapi-version',
    '--title',
    '--url',
    '--version',
    )
VALID_FLAGS = (
    *VALID_ARG_FLAGS,
    *VALID_KWARG_FLAGS,
    )

HELP_TEXT = '\n'.join(
    (
        'docent REST CLI - Usage',
        '-----------------------',
        ' '.join(
            (
                'Specify a python package for docent to parse for an API.',
                )
            ),
        ' '.join(
            (
                'Example: $ docent-convert docent.template.api',
                )
            ),
        '--------------------------------------',
        'VALID ARGUMENT FLAGS',
        ' '.join(
            (
                '--title={title}',
                '::',
                'App title.',
                )
            ),
        '  * DEFAULT = {python_package_api}.__name__',
        ' '.join(
            (
                '--version={version}',
                '::',
                'App version.',
                )
            ),
        '  * DEFAULT = {python_package_api}.__version__',
        ' '.join(
            (
                '--env={env}',
                '::',
                'App environment.',
                )
            ),
        '  * DEFAULT = dev',
        ' '.join(
            (
                '--url={url}',
                '::',
                'Deployment scheme and network address.',
                )
            ),
        "  * DEFAULT = os.getenv('HOST', 'localhost')",
        ' '.join(
            (
                '--openapi-version={version}',
                '::',
                'OpenAPI version to use.',
                )
            ),
        f'  * DEFAULT = {DEFAULT_OPENAPI_VERSION}',
        f'  * SUPPORTED = 3.0.*',
        ' '.join(
            (
                '--aws-lambda',
                '::',
                'Specifies whether or not deployment should include',
                'AWS Lambda {proxy+} route.',
                )
            ),
        ' '.join(
            (
                '--aws-api-gateway',
                '::',
                'Specifies whether or not deployment should account for',
                'AWS API Gateway requirements.',
                )
            ),
        ' '.join(
            (
                '--include-base-path',
                '::',
                'Whether or not to suffix primary URL with /{basePath}.',
                )
            ),
        ' '.join(
            (
                '--suffix-env',
                '::',
                'Whether or not to suffix environment to URL.',
                )
            ),
        ' '.join(
            (
                '--verbose (-v)',
                '::',
                'docent CLI output verbosity.',
                )
            ),
        '----------------------------',
        )
    )


def convert():
    """
    CLI entrypoint for converting an API's python code to a valid
    OpenAPI specification (output in yaml).

    ---

    Specify a python package for docent to parse for an API.

    ```sh
    $ docent-convert docent.template.api
    ```

    For detailed options:

    ```sh
    $ docent-convert --help
    ```

    """

    try:

        args = sys.argv

        from .. import utils

        spec = utils.spec_from_api(
            tuple(args),
            HELP_TEXT,
            VALID_FLAGS,
            VALID_KWARG_FLAGS,
            DEFAULT_OPENAPI_VERSION,
            DEFAULT_APP_VERSION,
            )

        title = spec['info']['title']
        version = spec['info']['version']

        yaml = ''
        for k in (
            'openapi',
            'info',
            'servers',
            'paths',
            'components',
            ):
            yaml += docent.core.utils.to_yaml({k: spec.pop(k)})

        for k in sorted(spec):
            yaml += docent.core.utils.to_yaml({k: spec.pop(k)})

        if '--verbose' in args or '-v' in args:
            docent.core.log.info(yaml)

        file_path = '-'.join((title, version)) + '.yaml'
        with open(file_path, 'w') as f:
            f.write(yaml)

        docent.core.log.info('docent --> OpenAPI.yaml :: SUCCESS')
        docent.core.log.info(f'API FILE :: {file_path}')
        docent.core.log.info(f'API FILE PATH :: {os.path.abspath(file_path)}')

    except:
        docent.core.log.error('For assistance: $ docent-convert --help')


def serve():
    """
    CLI entrypoint for serving an application.

    ---

    Specify the name of your API package to serve it via docent's \
    simple http server.

    ```sh
    $ docent-serve docent.template.api
    ```

    You may specify a port as a positional argument following \
    the package name. By default, your application will be served \
    on port 80, accessible at http://localhost/docs in your browser.

    ### DISCLAIMER
    `$ docent-serve` is highly insecure and should NOT be used \
    in any production environment.

    This may change in the future.
    """

    DEFAULT_PORT = 80

    if len(args := sys.argv) < 2:
        raise SyntaxError(
            "Please specify an importable 'python_package' to serve.",
            )
    else:
        _ = importlib.import_module(args[1])

    from .. import handler

    if len(args) > 2:
        port = int(args[2])
    else:
        port = DEFAULT_PORT

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.block_on_close = False
    socketserver.ThreadingTCPServer.daemon_threads = True

    with socketserver.ThreadingTCPServer(
        ('', port),
        handler.DocHandler
        ) as httpd:
        try:
            docent.core.log.info(f'SERVING PORT: {port} (Press CTRL+C to quit)')
            httpd.serve_forever()
        except KeyboardInterrupt:
            docent.core.log.info('Keyboard interrupt received, exiting.')
