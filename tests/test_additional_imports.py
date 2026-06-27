import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from et.infrastructure.additional_imports import (
    copy_additional_mods,
    resolve_additional_mod_files,
)


class AdditionalImportsTests(unittest.TestCase):
    def test_star_resolves_all_pak_files_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            (source_root / "A.pak").write_text("a", encoding="utf-8")
            nested = source_root / "nested"
            nested.mkdir()
            (nested / "B.pak").write_text("b", encoding="utf-8")
            (nested / "ignored.txt").write_text("ignored", encoding="utf-8")

            files, missing = resolve_additional_mod_files(source_root, ["*"])

            self.assertEqual([path.name for path in files], ["A.pak", "B.pak"])
            self.assertEqual(missing, [])

    def test_specific_entries_resolve_by_filename_and_stem(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            (source_root / "First.pak").write_text("first", encoding="utf-8")
            nested = source_root / "nested"
            nested.mkdir()
            (nested / "Second.pak").write_text("second", encoding="utf-8")

            files, missing = resolve_additional_mod_files(
                source_root,
                ["Second", "First.pak"],
            )

            self.assertEqual([path.name for path in files], ["Second.pak", "First.pak"])
            self.assertEqual(missing, [])

    def test_missing_specific_entries_are_reported_and_available_files_remain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            (source_root / "Available.pak").write_text("available", encoding="utf-8")

            files, missing = resolve_additional_mod_files(
                source_root,
                ["Available", "MissingMod"],
            )

            self.assertEqual([path.name for path in files], ["Available.pak"])
            self.assertEqual(missing, ["MissingMod"])

    def test_duplicate_names_use_first_sorted_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            alpha = source_root / "alpha"
            beta = source_root / "beta"
            alpha.mkdir()
            beta.mkdir()
            (beta / "Duplicate.pak").write_text("beta", encoding="utf-8")
            (alpha / "Duplicate.pak").write_text("alpha", encoding="utf-8")

            logger = Mock()
            with patch(
                "et.infrastructure.additional_imports.get_logger",
                return_value=logger,
            ):
                files, missing = resolve_additional_mod_files(source_root, ["Duplicate"])

            self.assertEqual(files, [alpha / "Duplicate.pak"])
            self.assertEqual(missing, [])
            logger.warning.assert_called_once()

    def test_star_uses_first_sorted_path_for_duplicate_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            alpha = source_root / "alpha"
            beta = source_root / "beta"
            alpha.mkdir()
            beta.mkdir()
            (beta / "Duplicate.pak").write_text("beta", encoding="utf-8")
            (alpha / "Duplicate.pak").write_text("alpha", encoding="utf-8")

            logger = Mock()
            with patch(
                "et.infrastructure.additional_imports.get_logger",
                return_value=logger,
            ):
                files, missing = resolve_additional_mod_files(source_root, ["*"])

            self.assertEqual(files, [alpha / "Duplicate.pak"])
            self.assertEqual(missing, [])
            logger.warning.assert_called_once()

    def test_copy_additional_mods_copies_flat_to_destination(self) -> None:
        with tempfile.TemporaryDirectory() as source_directory:
            with tempfile.TemporaryDirectory() as destination_directory:
                source_root = Path(source_directory)
                destination_root = Path(destination_directory)
                nested = source_root / "nested"
                nested.mkdir()
                source_path = nested / "NestedMod.pak"
                source_path.write_text("mod", encoding="utf-8")

                with patch(
                    "et.infrastructure.additional_imports.copy_with_progress",
                    side_effect=lambda pairs: [
                        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                        for source, destination in pairs
                    ],
                ):
                    copy_additional_mods(source_root, destination_root, ["NestedMod"])

                self.assertEqual(
                    (destination_root / "NestedMod.pak").read_text(encoding="utf-8"),
                    "mod",
                )

    def test_copy_additional_mods_uses_existing_overwrite_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as source_directory:
            with tempfile.TemporaryDirectory() as destination_directory:
                source_root = Path(source_directory)
                destination_root = Path(destination_directory)
                (source_root / "Existing.pak").write_text("new", encoding="utf-8")
                (destination_root / "Existing.pak").write_text("old", encoding="utf-8")

                progress = Mock()
                with patch(
                    "et.infrastructure.additional_imports.prompt_overwrite",
                    return_value="skip",
                ) as prompt:
                    with patch(
                        "et.infrastructure.additional_imports.copy_with_progress",
                        progress,
                    ):
                        copy_additional_mods(source_root, destination_root, ["Existing"])

                prompt.assert_called_once_with(destination_root / "Existing.pak")
                progress.assert_not_called()
                self.assertEqual(
                    (destination_root / "Existing.pak").read_text(encoding="utf-8"),
                    "old",
                )


if __name__ == "__main__":
    unittest.main()
