"""
Overview
--------

**Owner:** daniel.dube@annalect.com

**Maintainer:** daniel.dube@annalect.com

**Summary:** A simple python API that can be copy / pasted / replaced.


_This description was sourced from the docstring of the root \
level \_\_init\_\_.py file of the docent.template.api package._


"""

import docent.core
import docent.rest

# Note: API-wide settings need to be applied *before*
# you import your decorated resource definitions from
# relative modules (i.e. set below before doing any
# from . import ...).

docent.rest.APIMeta.AUTHORIZERS = [
    docent.rest.objects.security.Authorizer(
        name='x-docent-api-key',
        in_=docent.rest.enums.parameter.In.header.value,
        type=docent.rest.enums.security.SecurityScheme.apiKey.value,
        ),
    ]

from . import apis
from . import core

__version__ = docent.core.__version__


print('SOMEONE LEFT THIS PRINT STATEMENT AND FORGOT ABOUT IT')
print('GOOD THING DOCENT AUTOMATICALLY SILENCES PRINT STATEMENTS')
print('IF IT DETECTS AN ENV >= DEV.')
print('...')
print('THIS HELPS PREVENT LOG POLLUTION')
print('BEST PRACTICE IS TO USE A DEBUG LEVEL LOG MESSAGE INSTEAD')
