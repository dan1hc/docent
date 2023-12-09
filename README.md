# Overview

**Owner:** daniel.dube@annalect.com

**Maintainer:** daniel.dube@annalect.com

[**Documentation**](https://docent.1howardcapital.com/docent)

**Summary:** Zero-dependency python framework for object oriented development.
Implement _once_, document _once_, in _one_ place.

> A reimagining of a generic framework I originally began work
> on in-house at [Annalect](https://annalect.com)
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
> With Docent, you will quickly learn established best practice...
> or face the consequences of runtime errors that will break your code
> if you deviate from it.
>
> Experienced python engineers will find a framework
> that expects and rewards intuitive magic method implementations,
> consistent type annotations, and robust docstrings.
>
> Implement _pythonically_ with Docent and you will only ever need to:
> implement _once_, document _once_, in _one_ place.

---

## Getting Started

#### Installation
* Install from command line, with pip:

    `$ pip install docent`

* To install from source repository:

    ```sh
    $ git clone git@github.com:dan1hc/docent.git
    $ cd docent
    $ pip install .
    ```

#### The Template
* Docent ships with a template API and python package.
    * You can immediately run the template API from the command line with:
        * `$ docent-serve docent.template.api`
        * Access in your browser at [http://localhost/docs](http://localhost/docs)
    * We recommend new users copy / paste this template code and replace it with their own.

* Additionally, this repository itself is designed to serve as a lightweight template for
a well-organized python package repository. New users should feel free to clone it
and copy / paste contents for their needs.
    * See the `template/api` directory for a templatized example API.
    * See the `template/package` directory for a templatized example python package.
    * See the [`Repository Guide`](#repository-guide) below for more detail on
    structuring the source code repository of a python package.

---

## Usage Guidelines

* Import with absolute path to installed namespace package(s):

    ```py
    import docent.core
    ```

    ```py
    import docent.rest
    ```

* Serve an API created with Docent from command line on your local machine via:

    ```sh
    $ docent-serve name_of_your_api_package
    ```

    _The API must be an importable python package._

    ```py
    import name_of_your_api_package
    ```

---

## Planned Features

* #### Authentication / Authorization Framework
    * Although Docent supports the specification of auth components, there
    is currently no functionality that automatically validates a request against
    a specified authenticator / authorizer.
* #### Unit Tests
    * Docent is currently at approximately 0% code coverage and will
    need unit tests authored.
* #### Full OpenAPI Support
    * Docent will eventually support all aspects of an OpenAPI specification.
    Currently, certain functionality is not supported (and not necessarily
    documented).
* #### 3rd-party Integrations
    * Docent will offer extensions to make integrating with other commonly
    used tools easier. For example, a docent\[aws\] distribution is planned
    to help users get off the ground quickly with tools like AWS API Gateway
    and AWS Lambda.

---

## Features under Consideration

* #### Webserver Integration
    * While `$ docent-serve` leverages a simple webserver to make your
    application available for local development, this server is highly
    insecure and should _never_ be used in production.
    * It is currently up to the developer to integrate Docent applications
    with a third-party webserver for production. This may change.
* #### Framework Integration
    * Similar to the case for webserver integration (though likely
    mutually exclusive with it), it may be beneficial in the future to allow
    Docent to integrate with other, similar frameworks like FastAPI and Flask.

---

## Repository Guide

* docent
    * This directory contains the package itself.
* docs
    * This directory contains the documentation conf.py file
    and .rst templates used by Sphinx to auto-generate
    Docent's documentation wiki.
* LICENSE
    * The file containing the LICENSE for this software.
    You absolutely _should_ have one of these.
    * Docent's license, the GNU LGPL, allows for commercial
    use, but is not necessarily proprietary.
    * While I wanted to make Docent available for commerical use
    to the widest possible audience, in most cases,
    if you're employed by someone else, you will probably want to use a
    proprietary license.
* .gitignore
    * This .gitignore file is prepopulated with useful patterns for
    preventing unwanted files commonly generated during normal
    python development from being committed to source accidentally.
* README.md
    * The file you are currently reading. At a minimum, yours should
    contain enough information for an intended user to easily
    install and use your software in some meaningful way without
    additional assistance.
* requirements.txt
    * Empty since docent will never require dependencies. For packages
    that do require dependencies, this is where they should be
    specified.
        * Example contents if your package used the 'boto3' and 'requests'
        libraries (locked to major versions 1 and 2 respectively):
            ```
            boto3==1.*
            requests==2.*
            ```
* setup.py
    * Including a file called 'setup.py' at the root level of your python
    package's code repository is one way to make your package installable.
    See below for an example setup.py that will work well for most python
    packages.

        ```py
        import setuptools

        AUTHOR_EMAIL = 'daniel.dube@annalect.com'
        DESC = 'Example description.'
        PACKAGE_NAME = 'example_package'
        VERSION = '0.1.1.dev1'  # Should follow some form of semantic versioning.

        with open('requirements.txt', 'r') as f:
            INSTALL = f.readlines()

        if __name__ == '__main__':
            setuptools.setup(
                maintainer_email=AUTHOR_EMAIL,
                description=DESC,
                install_requires=INSTALL,  # This is what will actually force pip
                                           # to install any required dependencies,
                                           # not the requirements.txt file alone
                                           # (hence why we read the file above).
                license='LGPL',
                name=PACKAGE_NAME,
                packages=setuptools.find_packages(),  # This will 'find'
                                                      # your package; install
                                                      # will not do anything
                                                      # without this.
                python_version='>=3.8',
                version=VERSION,
                )
        ```

    * To install a package using a setup.py file from the command line,
    make sure you are in the same directory as the setup.py file and
    run the following command:
        * `$ pip install .`
    * If you are working on the python package locally yourself, plan
    to make edits to it, and do not want to have to frequently
    reinstall it:
        * Include the '-e' flag.
        * `$ pip install -e .`
