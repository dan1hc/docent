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

from . import apis
from . import core

__version__ = docent.core.__version__

docent.rest.APIMeta.AUTHORIZERS = [
    docent.rest.objects.security.Authorizer(
        name='x-docent-api-key',
        in_=docent.rest.enums.parameter.In.header.value,
        type=docent.rest.enums.security.SecurityScheme.apiKey.value,
        ),
    ]
