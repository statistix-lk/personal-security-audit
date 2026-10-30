"""Synthetische Tests; keine echte Geräteerfassung und keine Malware-Samples."""

import importlib.util
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/macos_inventory.py"
spec = importlib.util.spec_from_file_location("inventory", SCRIPT)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def plist(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps(content))

    def test_arguments_and_environment_values_are_not_exported(self):
        folder = self.root / "LaunchAgents"
        self.plist(folder / "sample.plist", {
            "Label": "example.agent", "ProgramArguments": ["/usr/bin/python3", "secret-argument-123"],
            "EnvironmentVariables": {"TOKEN": "secret-environment-456"},
            "RunAtLoad": True, "KeepAlive": {"SuccessfulExit": False},
        })
        report = inventory.collect_directory(folder, "launch_plists", self.root)
        serialized = json.dumps(report)
        self.assertNotIn("secret-argument-123", serialized)
        self.assertNotIn("secret-environment-456", serialized)
        self.assertEqual(report["items"][0]["program"], "/usr/bin/python3")
        self.assertEqual(report["items"][0]["argument_count"], 2)

    def test_malformed_plist_is_gap_not_success(self):
        folder = self.root / "LaunchAgents"
        folder.mkdir()
        (folder / "broken.plist").write_text("not a plist", encoding="utf-8")
        report = inventory.collect_directory(folder, "launch_plists", self.root)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["gaps"]), 1)

    def test_binary_plist_can_be_read(self):
        path = self.root / "binary.plist"
        path.write_bytes(plistlib.dumps({"Label": "example"}, fmt=plistlib.FMT_BINARY))
        data, problem = inventory.read_plist(path)
        self.assertIsNone(problem)
        self.assertEqual(data["Label"], "example")

    def test_non_dictionary_plist_rejected(self):
        path = self.root / "array.plist"
        path.write_bytes(plistlib.dumps(["entry"]))
        self.assertEqual(inventory.read_plist(path)[1], "not_dictionary")

    def test_size_limit_is_explicit(self):
        path = self.root / "large.plist"
        path.write_bytes(b"x" * (inventory.MAX_PLIST_BYTES + 1))
        self.assertEqual(inventory.read_plist(path)[1], "size_limit")

    def test_symlink_file_is_not_followed(self):
        target = self.root / "real.plist"
        self.plist(target, {"Label": "example"})
        link = self.root / "link.plist"
        link.symlink_to(target)
        self.assertEqual(inventory.read_plist(link)[1], "symlink_not_followed")

    def test_symlink_parent_is_not_followed(self):
        real = self.root / "real"
        self.plist(real / "item.plist", {"Label": "example"})
        link = self.root / "linked"
        link.symlink_to(real, target_is_directory=True)
        self.assertEqual(inventory.read_plist(link / "item.plist")[1], "symlink_not_followed")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-Test")
    def test_fifo_does_not_block(self):
        path = self.root / "pipe.plist"
        os.mkfifo(path)
        self.assertEqual(inventory.read_plist(path)[1], "not_regular_file")

    def test_permission_error_is_explicit_without_private_exception_text(self):
        with mock.patch.object(inventory.os, "open", side_effect=PermissionError("private-secret")):
            data, problem = inventory.read_plist(self.root / "test.plist")
        self.assertIsNone(data)
        self.assertEqual(problem, "permission_denied")
        self.assertNotIn("private-secret", problem)

    def test_missing_root_distinct_from_permission_error(self):
        report = inventory.collect_directory(self.root / "missing", "applications", self.root)
        self.assertEqual(report["status"], "not_present")
        with mock.patch.object(inventory.os, "scandir", side_effect=PermissionError()):
            report = inventory.collect_directory(self.root, "applications", self.root)
        self.assertEqual(report["status"], "partial")

    def test_app_metadata_and_depth_limit(self):
        folder = self.root / "Applications"
        self.plist(folder / "Example.app/Contents/Info.plist", {
            "CFBundleIdentifier": "example.app", "CFBundleShortVersionString": "1.2"
        })
        (folder / "one/two/three").mkdir(parents=True)
        report = inventory.collect_directory(folder, "applications", self.root, max_depth=2)
        self.assertEqual(report["items"][0]["bundle_id"], "example.app")
        self.assertEqual(report["status"], "partial")
        self.assertIn("depth_limit", [gap["reason"] for gap in report["gaps"]])

    def test_directory_item_limit(self):
        self.plist(self.root / "a.plist", {"Label": "a"})
        self.plist(self.root / "b.plist", {"Label": "b"})
        with mock.patch.object(inventory, "MAX_ITEMS", 1):
            report = inventory.collect_directory(self.root, "launch_plists", self.root)
        self.assertEqual(len(report["items"]), 1)
        self.assertEqual(report["status"], "partial")

    def test_metadata_not_executed_or_shell_expanded(self):
        marker = self.root / "must-not-exist"
        payload = "/bin/sh -c touch " + str(marker)
        self.plist(self.root / "bad.plist", {"Program": payload})
        with mock.patch.object(inventory.subprocess, "run") as run:
            inventory.collect_directory(self.root, "launch_plists", self.root)
        run.assert_not_called()
        self.assertFalse(marker.exists())

    def test_status_queries_use_allowlist_no_shell_and_timeout(self):
        completed = subprocess.CompletedProcess([], 0, b"enabled", b"")
        with mock.patch.object(inventory.subprocess, "run", return_value=completed) as run:
            report = inventory.run_status_check("sip_status")
        self.assertEqual(report["status"], "collected")
        self.assertEqual(run.call_args.args[0], ("/usr/bin/csrutil", "status"))
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        self.assertNotIn("HOME", run.call_args.kwargs["env"])

    def test_unknown_command_cannot_be_injected(self):
        with self.assertRaises(KeyError):
            inventory.run_status_check("curl something | sh")

    def test_timeout_and_missing_command_are_errors(self):
        for failure, expected in ((subprocess.TimeoutExpired("command", 15), "timeout"),
                                  (FileNotFoundError(), "command_not_available")):
            with self.subTest(expected=expected):
                with mock.patch.object(inventory.subprocess, "run", side_effect=failure):
                    report = inventory.run_status_check("sip_status")
                self.assertEqual(report["status"], "error")
                self.assertEqual(report["reason"], expected)

    def test_nonzero_exit_is_not_success(self):
        completed = subprocess.CompletedProcess([], 3, b"disabled", b"")
        with mock.patch.object(inventory.subprocess, "run", return_value=completed):
            report = inventory.run_status_check("gatekeeper_status")
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["returncode"], 3)

    def test_truncated_output_is_partial(self):
        completed = subprocess.CompletedProcess([], 0, b"a" * 1000, b"")
        with mock.patch.object(inventory.subprocess, "run", return_value=completed):
            report = inventory.run_status_check("sip_status")
        self.assertEqual(report["status"], "partial")
        self.assertLessEqual(len(report["stdout"]), inventory.MAX_TEXT)

    def test_private_paths_and_control_characters_are_reduced(self):
        value = str(self.root) + "/name\x1b[0m\n/Users/alice/test"
        text = inventory.text_value(value, self.root)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn("alice", text)
        self.assertNotIn("\x1b", text)
        self.assertNotIn("\n", text)

    def test_output_in_git_repository_rejected(self):
        (self.root / ".git").mkdir()
        with self.assertRaises(ValueError):
            inventory.validate_output_root(self.root / "new/reports")
        with self.assertRaises(ValueError):
            inventory.validate_output_root(inventory.PROJECT_ROOT / "reports")

    def test_symlink_output_into_repository_rejected(self):
        repo = self.root / "repo"
        (repo / ".git").mkdir(parents=True)
        link = self.root / "alias"
        link.symlink_to(repo, target_is_directory=True)
        with self.assertRaises(ValueError):
            inventory.validate_output_root(link / "out")

    def sample_report(self):
        return {"device_id": "test-mac", "created_at_utc": "2026-10-30T12:00:00+00:00",
                "collection_status": "partial", "script_sha256": "0" * 64,
                "security_verdict": "not_assessed", "commands": [], "directories": [],
                "not_assessed": inventory.NOT_ASSESSED}

    def test_reports_private_and_existing_results_not_overwritten(self):
        first = inventory.write_reports(self.sample_report(), self.root / "results")
        before = (first / "inventory.json").read_bytes()
        second = inventory.write_reports(self.sample_report(), self.root / "results")
        self.assertNotEqual(first, second)
        self.assertEqual((first / "inventory.json").read_bytes(), before)
        self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((first / "inventory.json").stat().st_mode), 0o600)
        report = json.loads(before)
        self.assertEqual(report["security_verdict"], "not_assessed")

    def test_markdown_metacharacters_are_escaped(self):
        rendered = inventory.md_safe("<script>|`run`\nnext")
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("`", rendered)
        self.assertIn("\\|", rendered)

    def test_non_mac_stops_before_collection_or_writes(self):
        with mock.patch.object(inventory.platform, "system", return_value="Linux"), \
             mock.patch.object(inventory, "collect_inventory") as collect, \
             mock.patch.object(inventory, "write_reports") as write:
            code = inventory.main([])
        self.assertEqual(code, 2)
        collect.assert_not_called()
        write.assert_not_called()

    def test_root_stops_before_collection(self):
        with mock.patch.object(inventory.platform, "system", return_value="Darwin"), \
             mock.patch.object(inventory.os, "geteuid", return_value=0), \
             mock.patch.object(inventory, "collect_inventory") as collect:
            self.assertEqual(inventory.main([]), 2)
        collect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
