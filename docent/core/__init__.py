"""
Overview
========

**Owner:** daniel.dube@annalect.com

**Maintainer:** daniel.dube@annalect.com

**Summary:** Zero-dependency python framework for object oriented development.

---

Usage
-----

Import with absolute path to installed namespace package(s).

```py
import docent.core
```

"""

from . import constants
from . import exceptions
from . import logger
from . import objects
from . import types
from . import utils

from .constants import PackageConstants as Constants
from .objects import DocObject
from .types import DocMeta

__version__ = '0.0.1a5'

log = logger.get_central_log()
