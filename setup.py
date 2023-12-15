import importlib
import setuptools

AUTHOR = 'Dan'
AUTHOR_EMAIL = 'daniel.dube@annalect.com'
DESC = 'Zero-dependency Python framework for object oriented development.'
DESC_LONG = ' '.join(
    (
        'Zero-dependency Python framework for object oriented development.',
        '\n',
        'A reimagining of a generic framework I originally',
        'began work on in-house at Annalect.',
        '\n',
        'Re-imagined and completed as a personal project in an effort',
        'to both benefit the widest possible audience and make',
        'installations themselves easier across Annalect',
        'and all other Omnicom Group subsidiaries via',
        "publication to the Python Software Foundation's",
        'publicly distributed Python Package Index.',
        '\n',
        'Forces users to adopt best practices in code structure,',
        'documentation, object oriented programming, RESTfulness,',
        'and the python language.',
        )
    )
PACKAGE_NAME = 'docent'
VERSION = importlib.import_module('docent.core').__version__

with open('requirements.txt', 'r') as f:
    INSTALL = f.readlines()

if __name__ == '__main__':
    setuptools.setup(
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=AUTHOR,
        maintainer_email=AUTHOR_EMAIL,
        classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',  # noqa
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
            'Programming Language :: Python :: 3.13',
            'Topic :: Software Development :: Libraries :: Application Frameworks',  # noqa
            'Typing :: Typed',
            ],
        description=DESC,
        download_url=f'https://github.com/dan1hc/{PACKAGE_NAME}',
        long_description=DESC_LONG,
        entry_points={
            'console_scripts': [
                'docent-convert=docent.rest.commands:convert',
                'docent-document=docent.docs.commands:document',
                'docent-serve=docent.rest.commands:serve',
                ]
            },
        extras_require={
            'core': [],
            'docs': [
                'commonmark==0.*',
                'pydata_sphinx_theme==0.*',
                'sphinx==7.*',
                ],
            'rest': [
                'docent[core]'
                ],
            'template': [
                'docent[core]',
                'docent[rest]'
                ],
            },
        install_requires=INSTALL,
        license='LGPL',
        name=PACKAGE_NAME,
        packages=setuptools.find_namespace_packages(),
        package_data={
            '.'.join((PACKAGE_NAME, 'docs', 'static')): [
                '*'
                ],
            '.'.join((PACKAGE_NAME, 'rest', 'static')): [
                '*'
                ],
            },
        python_version='>=3.9',
        url=f'https://{PACKAGE_NAME}.1howardcapital.com/{PACKAGE_NAME}',
        version=VERSION,
        )
