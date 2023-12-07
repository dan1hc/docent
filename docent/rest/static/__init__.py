"""Static files (html and icons)."""

__all__ = (
    'HTML',
    'ICON',
    'ICON16',
    'ICON32',
    )

_root = __file__.replace('__init__.py', '')

with open('/'.join((_root, 'swagger.html')), 'r') as f:
    HTML = f.read()

with open('/'.join((_root, 'favicon.ico')), 'rb') as f:
    ICON = f.read()

with open('/'.join((_root, 'favicon-16x16.png')), 'rb') as f:
    ICON16 = f.read()

with open('/'.join((_root, 'favicon-32x32.png')), 'rb') as f:
    ICON32 = f.read()
