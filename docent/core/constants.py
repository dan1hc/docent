import os


class PackageConstants:
    """Constant values across all of docent."""

    DOC_DELIM      = '-'
    ENV            = os.getenv('ENV', 'local').lower()
    FTIME_DEFAULT  = '%Y-%m-%dT%H:%M:%S.%f%z'
    FTIME_LOG      = '%Y-%m-%d %H:%M:%S'
    FTIME_LOG_MSEC = '%s.%03d UTC'
    FTIME_US_YEAR  = '%Y-%m-%d'
    INDENT         = int(os.getenv('LOG_INDENT', 2))
    LOG_CUTOFF_LEN = int(os.getenv('LOG_CUTOFF_LEN', 1024))
    LOG_LEVEL      = os.getenv(
        'LOG_LEVEL',
        'DEBUG' if ENV in {'dev', 'develop', 'local'} else 'INFO'
        ).upper()
    NEW_LINE_TOKEN = '||N'
    RE_JSON        = r'((?<!\\)\+)'
