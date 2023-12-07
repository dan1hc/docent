import commonmark


def docstring(app, what, name, obj, options, lines):  # noqa
    md  = '\n'.join(lines)
    ast = commonmark.Parser().parse(md)
    rst: str = commonmark.ReStructuredTextRenderer().render(ast)
    lines[:] = rst.splitlines()


def setup(app):  # noqa
    app.connect('autodoc-process-docstring', docstring)


master_doc = project = '${package_name}'
author = '${author_name}'
release = '${package_version}'
copyright = author

autodoc_inherit_docstrings = False
extensions = [
    'sphinx.ext.autodoc',
    ]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_favicon = './_static/favicon.ico'
html_logo = './_static/logo.png'
html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
