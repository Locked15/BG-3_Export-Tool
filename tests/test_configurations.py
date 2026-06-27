import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from et.infrastructure.configurations import _resolve_conflicts


class ConfigurationConflictTests(unittest.TestCase):
    def test_overwrite_always_applies_to_remaining_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination_one = root / "one.json"
            destination_two = root / "two.json"
            destination_one.write_text("old one", encoding="utf-8")
            destination_two.write_text("old two", encoding="utf-8")
            files_to_copy = [
                (root / "source-one.json", destination_one),
                (root / "source-two.json", destination_two),
            ]

            with patch(
                "et.infrastructure.configurations.prompt_choice",
                return_value="Overwrite always",
            ) as prompt:
                resolved = _resolve_conflicts(files_to_copy)

            self.assertEqual(resolved, files_to_copy)
            prompt.assert_called_once()

    def test_ignore_always_applies_to_remaining_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination_one = root / "one.json"
            destination_two = root / "two.json"
            destination_one.write_text("old one", encoding="utf-8")
            destination_two.write_text("old two", encoding="utf-8")
            files_to_copy = [
                (root / "source-one.json", destination_one),
                (root / "source-two.json", destination_two),
            ]

            with patch(
                "et.infrastructure.configurations.prompt_choice",
                return_value="Ignore always",
            ) as prompt:
                resolved = _resolve_conflicts(files_to_copy)

            self.assertEqual(resolved, [])
            prompt.assert_called_once()

    def test_ignore_skips_only_selected_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination_one = root / "one.json"
            destination_two = root / "two.json"
            destination_one.write_text("old one", encoding="utf-8")
            destination_two.write_text("old two", encoding="utf-8")
            files_to_copy = [
                (root / "source-one.json", destination_one),
                (root / "source-two.json", destination_two),
            ]

            with patch(
                "et.infrastructure.configurations.prompt_choice",
                side_effect=["Ignore", "Overwrite"],
            ):
                resolved = _resolve_conflicts(files_to_copy)

            self.assertEqual(resolved, [files_to_copy[1]])


if __name__ == "__main__":
    unittest.main()
