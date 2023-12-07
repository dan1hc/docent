import unittest


class TestImport(unittest.TestCase):
    """Fixture for testing importing the module."""

    def test_can_import_module(self):
        """Test whether or not importing the module succeeds."""

        try:
            import docent.rest
        except (ModuleNotFoundError, ImportError):
            self.assertTrue(False)
        except Exception as e:
            raise e
        else:
            self.assertTrue(True)
