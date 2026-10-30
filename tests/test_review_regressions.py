"""Drei offene Review-Befunde; nur künstliche Dateien, keine Geräteerfassung.

expectedFailure dokumentiert den unverändert archivierten Fehlerzustand.
Nach einer Korrektur die jeweilige Markierung entfernen, nicht den Test löschen.
"""

import importlib.util
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "review_inventory", ROOT / "scripts/macos_inventory.py"
)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class ReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    @unittest.expectedFailure
    def test_r1_output_must_not_follow_replaced_directory_into_repository(self):
        output = self.root / "output"
        output.mkdir()
        repo = self.root / "synthetic-repo"
        (repo / ".git").mkdir(parents=True)
        original_mkdtemp = tempfile.mkdtemp

        def replace_output(*args, **kwargs):
            output.rename(self.root / "original-output")
            output.symlink_to(repo, target_is_directory=True)
            return original_mkdtemp(*args, **kwargs)

        report = {
            "device_id": "synthetic-test",
            "created_at_utc": "2026-10-30T00:00:00+00:00",
            "collection_status": "partial", "script_sha256": "0" * 64,
            "security_verdict": "not_assessed", "commands": [],
            "directories": [], "not_assessed": [],
        }
        with mock.patch.object(inventory.tempfile, "mkdtemp", side_effect=replace_output):
            try:
                inventory.write_reports(report, output)
            except (OSError, ValueError):
                pass  # Ein sicherer Abbruch ist zulässig.
        self.assertEqual(list(repo.glob("inventory-*/inventory.json")), [])
        self.assertEqual(list(repo.glob("inventory-*/summary.md")), [])

    @unittest.expectedFailure
    def test_r2_plist_must_not_be_read_through_replaced_parent(self):
        source = self.root / "source"
        other = self.root / "other"
        source.mkdir()
        other.mkdir()
        (source / "item.plist").write_bytes(plistlib.dumps({"Label": "expected"}))
        (other / "item.plist").write_bytes(plistlib.dumps({"Label": "outside"}))
        original_open = os.open
        changed = False

        def replace_parent(path, flags, *args, **kwargs):
            nonlocal changed
            if Path(path) == source / "item.plist" and not changed:
                source.rename(self.root / "original-source")
                source.symlink_to(other, target_is_directory=True)
                changed = True
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(inventory.os, "open", side_effect=replace_parent):
            data, problem = inventory.read_plist(source / "item.plist")
        self.assertNotEqual(data, {"Label": "outside"})

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-Test")
    @unittest.expectedFailure
    def test_r3_repository_guard_must_reject_fifo_without_blocking(self):
        os.mkfifo(self.root / "README.md")
        # Ein isolierter Kindprozess begrenzt den bekannten Hänger. subprocess.run
        # beendet ihn beim Timeout; keine Hintergrundprozesse bleiben bestehen.
        child = (
            "import importlib.util, json, sys; from pathlib import Path; "
            "s=importlib.util.spec_from_file_location('guard',sys.argv[1]); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "print(json.dumps(m.inspect_tree(Path(sys.argv[2]))))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", child,
             str(ROOT / "scripts/check_repository.py"), str(self.root)],
            capture_output=True, timeout=2, check=True,
        )
        self.assertNotEqual(completed.stdout.strip(), b"[]")


if __name__ == "__main__":
    unittest.main()
