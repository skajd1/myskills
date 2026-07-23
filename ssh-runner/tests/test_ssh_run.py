import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ssh_run.py"


spec = importlib.util.spec_from_file_location("ssh_run", SCRIPT_PATH)
ssh_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = ssh_run
spec.loader.exec_module(ssh_run)


class ParseArgsTests(unittest.TestCase):
    def test_double_dash_separator_is_not_part_of_remote_command(self):
        args = ssh_run.parse_args(
            ["--target", "85", "--", "uname -a"]
        )

        self.assertEqual(ssh_run.normalize_remote_command(args.remote_command), "uname -a")

    def test_remote_command_without_separator_still_works(self):
        args = ssh_run.parse_args(
            ["--target", "85", "df -h"]
        )

        self.assertEqual(ssh_run.normalize_remote_command(args.remote_command), "df -h")

    def test_build_command_uses_only_the_selected_identity(self):
        args = ssh_run.parse_args(["--target", "85", "--", "true"])

        with mock.patch.object(ssh_run.shutil, "which", return_value="ssh.exe"):
            command = ssh_run.build_ssh_command(args)

        self.assertIn(str(Path.home() / ".ssh" / "uface_id_rsa"), command)
        self.assertIn(str(SCRIPT_PATH.parents[1] / "config" / "hosts.conf"), command)
        self.assertIn("BatchMode=yes", command)
        self.assertIn("IdentitiesOnly=yes", command)
        self.assertNotIn("paramiko", " ".join(command).lower())


if __name__ == "__main__":
    unittest.main()
