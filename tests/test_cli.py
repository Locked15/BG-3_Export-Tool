import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from et import app as et_app
from et.domain.errors import ExporterError


class CliTests(unittest.TestCase):
    def test_no_args_prints_help_manual(self) -> None:
        result = CliRunner().invoke(et_app.app, [])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("init-session", result.output)

    def test_init_session_uses_default_config(self) -> None:
        with patch("et.app.run_export") as run_export:
            result = CliRunner().invoke(et_app.app, ["init-session"])

        self.assertEqual(result.exit_code, 0)
        run_export.assert_called_once_with(Path("config.json"))

    def test_init_session_accepts_config_override(self) -> None:
        with patch("et.app.run_export") as run_export:
            result = CliRunner().invoke(
                et_app.app,
                ["init-session", "--config", "custom.json"],
            )

        self.assertEqual(result.exit_code, 0)
        run_export.assert_called_once_with(Path("custom.json"))

    def test_exporter_error_exits_with_error(self) -> None:
        with patch("et.app.run_export", side_effect=ExporterError("bad config")):
            with patch("et.app.print_error") as print_error:
                result = CliRunner().invoke(et_app.app, ["init-session"])

        self.assertEqual(result.exit_code, 1)
        print_error.assert_called_once_with("bad config")

    def test_keyboard_interrupt_exits_with_error(self) -> None:
        with patch("et.app.run_export", side_effect=KeyboardInterrupt):
            with patch("et.app.print_cancelled") as print_cancelled:
                result = CliRunner().invoke(et_app.app, ["init-session"])

        self.assertEqual(result.exit_code, 1)
        print_cancelled.assert_called_once_with()


class LegacyCompatibilityTests(unittest.TestCase):
    def test_legacy_entrypoint_preserves_config_option(self) -> None:
        from et import migration_compatibility_patch

        with patch.object(
            sys,
            "argv",
            ["et-export", "--config", "legacy.json"],
        ):
            with patch("et.migration_compatibility_patch.run_export") as run_export:
                migration_compatibility_patch.main()

        run_export.assert_called_once_with(Path("legacy.json"))


if __name__ == "__main__":
    unittest.main()
