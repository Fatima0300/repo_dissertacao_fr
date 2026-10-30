import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.api_keys import get_api_key


class ApiKeyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env_file = Path(self.tmp.name) / ".env"
        # BOM, comment and quotes, as Windows Notepad may leave them
        self.env_file.write_text("﻿# comment\n\nTEST_KEY='from-file'\n", encoding="utf-8")

    def test_reads_env_file(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("TEST_KEY", None)
            self.assertEqual(get_api_key("TEST_KEY", self.env_file), "from-file")

    def test_environment_variable_has_priority(self):
        with mock.patch.dict(os.environ, {"TEST_KEY": "from-system"}):
            self.assertEqual(get_api_key("TEST_KEY", self.env_file), "from-system")

    def test_missing_key_fails_without_showing_values(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("MISSING_KEY", None)
            with self.assertRaises(LookupError) as error:
                get_api_key("MISSING_KEY", self.env_file)
        self.assertNotIn("from-file", str(error.exception))


if __name__ == "__main__":
    unittest.main()
