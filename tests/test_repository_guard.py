import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_repository.py"
spec = importlib.util.spec_from_file_location("guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class RepositoryGuardTests(unittest.TestCase):
    def test_raw_report_path_rejected(self):
        self.assertFalse(guard.allowed_path(Path("reports/inventory.json")))
        self.assertFalse(guard.allowed_path(Path("raw/data.md")))
        self.assertTrue(guard.allowed_path(Path("templates/report.md")))

    def test_known_secret_found_without_printing_value(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake = "gh" + "p_" + "A" * 36
            (root / "README.md").write_text(fake, encoding="utf-8")
            issues = guard.inspect_tree(root)
        self.assertEqual(len(issues), 1)
        self.assertNotIn(fake, str(issues))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("example", encoding="utf-8")
            (root / "alias.md").symlink_to(root / "README.md")
            issues = guard.inspect_tree(root)
        self.assertEqual(len(issues), 1)
        self.assertIn("Symlink", issues[0][1])


if __name__ == "__main__":
    unittest.main()
