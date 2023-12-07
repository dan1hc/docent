"""Static files (sphinx conf.py, favicon.ico, logo.png)."""

__all__ = (
    'CONF',
    )

_root = __file__.replace('__init__.py', '')

with open('/'.join((_root, 'conf.tpl')), 'r') as f:
    CONF = f.read()
