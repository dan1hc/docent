import os


class PackageConstants:
    """Constants to be shared across the entire package."""

    HOST = os.getenv('HOST', '/')
    APP  = os.getenv('APP', 'template')


os.environ['HOST'] = PackageConstants.HOST  # set to app url to enable /docs, '/' for local
os.environ['APP'] = PackageConstants.APP  # set to automatically include app name in logs
