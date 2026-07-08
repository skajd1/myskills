import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ssh_run.py"


spec = importlib.util.spec_from_file_location("ssh_run", SCRIPT_PATH)
ssh_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = ssh_run
spec.loader.exec_module(ssh_run)


class ParseArgsTests(unittest.TestCase):
    def test_double_dash_separator_is_not_part_of_remote_command(self):
        args = ssh_run.parse_args(["--target", "user@example.com", "--", "uname -a"])

        self.assertEqual(ssh_run.normalize_remote_command(args.remote_command), "uname -a")

    def test_remote_command_without_separator_still_works(self):
        args = ssh_run.parse_args(["--target", "user@example.com", "df -h"])

        self.assertEqual(ssh_run.normalize_remote_command(args.remote_command), "df -h")


if __name__ == "__main__":
    unittest.main()
