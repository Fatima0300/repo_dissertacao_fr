import json
import tempfile
import unittest
from pathlib import Path

from scripts.reproducibility import sha256, validate_comparison


class ComparisonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.before = root / "before" / "results.xlsx"
        self.after = root / "after" / "results.xlsx"
        for file, experiment in ((self.before, "previous"), (self.after, "current")):
            file.parent.mkdir()
            file.write_bytes(b"content")
            manifest = {
                "experiment": experiment,
                "excel_sha256": sha256(file),
                "inputs_sha256": {"data.csv": "abc"},
                "model": "model",
                "model_revision": "123",
                "seed": 42,
                "python": "3.13",
                "platform": "win-64",
                "packages": {"numpy": "2.3"},
            }
            (file.parent / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_same_run_accepted(self):
        validate_comparison(self.before, self.after, "previous", "current")

    def test_missing_file_fails(self):
        self.before.unlink()
        with self.assertRaises(FileNotFoundError):
            validate_comparison(self.before, self.after, "previous", "current")

    def test_stale_excel_fails(self):
        self.after.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            validate_comparison(self.before, self.after, "previous", "current")

    def test_different_data_fails(self):
        path = self.after.parent / "run_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["inputs_sha256"]["data.csv"] = "different"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inputs_sha256"):
            validate_comparison(self.before, self.after, "previous", "current")


if __name__ == "__main__":
    unittest.main()
