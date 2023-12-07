import importlib
import os
import shutil
import string
import sys

from .. import static


def _do_api_doc(
    package: str,
    output_dir: str,
    is_namespace_package: bool = False,
    ):

    os.environ['SPHINX_APIDOC_OPTIONS'] = 'members'

    try:
        import commonmark
        import pydata_sphinx_theme
        import sphinx.cmd.build
        import sphinx.ext.apidoc
    except ImportError:
        raise ImportError(
            '\n'.join(
                (
                    "Missing a required third-party dependency.",
                    "Install with `$ pip install docent[docs]`.",
                    ' '.join(
                        (
                            "Or with `$ pip install -e \".[docs]\"`",
                            "if you installed 'docent' from a local",
                            'repository clone.'
                            )
                        ),
                    'Exiting...'
                    )
                )
            )

    if os.path.exists(f'{output_dir}/docs'):
        shutil.rmtree(f'{output_dir}/docs')
    os.makedirs(f'{output_dir}/docs/source/_static')

    if is_namespace_package:
        sphinx.ext.apidoc.main(
            (
                '-d',
                '2',
                '-E',
                '-f',
                '-M',
                '--tocfile',
                'index',
                '--implicit-namespaces',
                '-o',
                f'{output_dir}/docs/source',
                package.strip('.').strip('/').replace('/', '.').split('.')[0],
                )
            )
    else:
        sphinx.ext.apidoc.main(
            (
                '-d',
                '2',
                '-E',
                '-f',
                '-M',
                '--tocfile',
                'index',
                '-o',
                f'{output_dir}/docs/source',
                package,
                )
            )


def _export_conf(
    package: str,
    author: str,
    output_dir: str,
    ):

    if '/' in package:
        _package = package.strip('.').strip('/')
        package_version = importlib.import_module(
            '.' + '.'.join(_package.split('/')[1:]),
            _package.split('/')[0],
            ).__version__
        package = _package.replace('/', '.')
    else:
        package_version = importlib.import_module(package).__version__

    template = string.Template(static.CONF)
    rendered = template.safe_substitute(
        {
            'package_name': package,
            'package_version': package_version,
            'author_name': author,
            }
        )

    with open(f'{output_dir}/docs/source/conf.py', 'w') as f:
        f.write(rendered)


def _do_build(
    output_dir: str,
    ):

    import sphinx.cmd.build

    sphinx.cmd.build.main(
        (
            '-a',
            '-E',
            f'{output_dir}/docs/source',
            f'{output_dir}/docs',
            )
        )


def document():
    """
    CLI entrypoint for documenting a python package in wiki style.

    Leverages and requires the Sphinx library and several supporting, \
    third-party dependencies. They can be installed using the following \
    command.

    ```sh
    $ pip install docent[docs]
    ```

    Or if you installed docent from a repository.

    ```sh
    $ pip install -e ".[docs]"
    ```

    ---

    Specify the name of the package (or path to the package) as the first \
    positional argument.

    ---

    To document the example `docent.template.package`, run the following \
    command from the root of docent's source code repository. The \
    '--namespace-package' flag is required where docent is a namespace \
    package (most python packages are not).

    ```sh
    $ docent-document ./docent/template/package --output . --namespace-package
    ```

    This will create a 'docs' sub-directory in the '--output' directory \
    specified (itself, relative to the directory from which the script \
    is executed).

    """

    package = sys.argv[1]

    if len(sys.argv) > 2:
        is_output_dir = False
        for i, a in enumerate(sys.argv[2:]):
            if a in {'-o', '--output'}:
                is_output_dir = True
                break

        if is_output_dir:
            output_dir = sys.argv[i + 3]
        else:
            output_dir = '.'

        is_author = False
        for i, a in enumerate(sys.argv[2:]):
            if a in {'-a', '--author'}:
                is_author = True
                break

        if is_author:
            author = sys.argv[i + 3]
        else:
            author = os.getlogin()

        is_namespace_package = '--namespace-package' in sys.argv
    else:
        output_dir = '.'
        author = os.getlogin()
        is_namespace_package  = False

    _do_api_doc(
        package,
        output_dir,
        is_namespace_package
        )

    static_dir = f'{output_dir}/docs/source/_static'
    shutil.copyfile(
        f'{static._root}/favicon.ico',
        f'{static_dir}/favicon.ico',
        )
    shutil.copyfile(
        f'{static._root}/logo.png',
        f'{static_dir}/logo.png',
        )

    # Below is done to fix static asset rendering on github pages.
    # See: https://github.com/sphinx-doc/sphinx/issues/2202
    with open(f'{output_dir}/docs/.nojekyll', 'w') as f:
        f.write('')

    if is_namespace_package:
        doc_root = package.strip('.').strip('/').replace('/', '.')
        for f in os.listdir(f'{output_dir}/docs/source'):
            if (
                f.endswith('.rst')
                and not f.endswith('index.rst')
                and not f.startswith(doc_root)
                ):
                os.remove(f'{output_dir}/docs/source/{f}')

    _export_conf(
        package,
        author,
        output_dir,
        )

    _do_build(
        output_dir,
        )

    shutil.rmtree(f'{output_dir}/docs/source')
