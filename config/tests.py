"""Regression checks for the local development server configuration."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from django.test import SimpleTestCase


class DevelopmentSettingsTests(SimpleTestCase):
    def load_debug_setting(self, command, debug_value=None):
        """Import settings without this checkout's optional .env file."""
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "isolated_config"
            package.mkdir()
            (package / "__init__.py").touch()
            shutil.copyfile(Path(__file__).with_name("settings.py"), package / "settings.py")

            environment = os.environ.copy()
            environment.pop("DJANGO_DEBUG", None)
            if debug_value is not None:
                environment["DJANGO_DEBUG"] = debug_value

            script = (
                "import sys; "
                f"sys.path.insert(0, {directory!r}); "
                f"sys.argv = ['manage.py', {command!r}]; "
                "from isolated_config.settings import DEBUG; print(DEBUG)"
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

    def test_runserver_enables_debug_without_env_file(self):
        self.assertEqual(self.load_debug_setting("runserver"), "True")

    def test_non_development_command_keeps_debug_disabled_by_default(self):
        self.assertEqual(self.load_debug_setting("check"), "False")

    def test_explicit_debug_false_overrides_runserver_default(self):
        self.assertEqual(self.load_debug_setting("runserver", "false"), "False")
