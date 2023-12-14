"""
Overview
========

**Owner:** daniel.dube@annalect.com

**Maintainer:** daniel.dube@annalect.com

**Summary:** Zero-dependency python framework for developing RESTful
APIs with python, the pythonic way.

---

Usage
-----

##### Import with absolute path to installed namespace package.

```py
import docent.rest
```

##### Serve an API created with docent from command line on your local machine.

```sh
$ docent-serve name_of_your_api_package
```

_The API must be an importable python package._

```py
import name_of_your_api_package
```

"""

import docent.core

from . import constants
from . import enums
from . import exceptions
from . import handler
from . import healthz
from . import objects
from . import resource
from . import route
from . import utils

from .objects import (
    Component,
    ComponentMeta,
    Request,
    )
from .resource import (
    Resource,
    )
from .route import (
    Route,
    RouteMeta,
    )

__version__ = docent.core.__version__
