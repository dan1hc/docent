"""
Overview
========

**Owner:** daniel.dube@annalect.com

**Maintainer:** daniel.dube@annalect.com

**Summary:** Zero-dependency python framework for object oriented development.
Implement _once_, document _once_, in _one_ place.

---

> A reimagining of a generic framework I originally began
> work on in-house at [Annalect](https://annalect.com)
> to speed development time for experienced python engineers
> while serving as a coercive template that forces its users
> to adopt best practices in code structure, documentation,
> object oriented programming, RESTfulness, and the python language.
>
> Re-imagined and completed as a personal project in an effort
> to both benefit the widest possible audience and make
> installations themselves easier across Annalect
> and all other [Omnicom Group](https://omnicomgroup.com)
> subsidiaries via publication to the Python Software Foundation's
> publicly distributed Python Package Index.
>
> With docent, you will quickly learn established best practice...
> or face the consequences of runtime errors that will break your code
> if you deviate from it.
>
> Experienced python engineers will find a framework
> that expects and rewards intuitive magic method implementations,
> consistent type annotations, and robust docstrings.
>
> Implement _pythonically_ with docent and you will only ever need to:
> implement _once_, document _once_, in _one_ place.

---

Getting Started
---------------

### Installation

Install from command line, with pip:

`$ pip install docent`

To install from source repository:

```sh
$ git clone git@github.com:dan1hc/docent.git
$ cd docent
$ pip install .
```

### The Template

docent ships with a template API and python package. \
You can immediately run the template API from the command line with:

```sh
$ docent-serve docent.template.api
```

Access in your browser at [http://localhost/docs](http://localhost/docs).


* We recommend new users copy / paste this template code and replace it with their own.

* Additionally, the repository itself is designed to serve as a lightweight template for \
a well-organized python package repository. New users should feel free to clone it \
and copy / paste contents for their needs.

* See the `template/api` directory for a templatized example API.

* See the `template/package` directory for a templatized example python package.

"""

from . import core

__version__ = core.__version__
