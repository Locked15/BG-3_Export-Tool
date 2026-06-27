import json
import tempfile
import unittest
from pathlib import Path

from et.domain.errors import ExporterError
from et.infrastructure.config import load_config


def write_config(path: Path, extra: dict[str, object] | None = None) -> None:
    config: dict[str, object] = {
        "mo2_profiles_path": "profiles",
        "mo2_mods_path": "mods",
        "bg3mm_orders_path": "orders",
        "bg3_native_mods_path": "native",
        "configurations_source_path": "source",
        "configurations_destination_path": "destination",
    }
    if extra:
        config.update(extra)
    path.write_text(json.dumps(config), encoding="utf-8")


class ConfigTests(unittest.TestCase):
    def test_additional_import_config_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            write_config(config_path)

            config = load_config(config_path)

            self.assertEqual(config["additional_mods_import"], [])
            self.assertEqual(
                config["additional_mods_import_path"],
                str(Path(directory) / "import"),
            )

    def test_relative_additional_import_path_resolves_from_config_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "nested" / "config.json"
            config_path.parent.mkdir()
            write_config(
                config_path,
                {
                    "additional_mods_import_path": "extra-imports",
                    "additional_mods_import": ["*"],
                },
            )

            config = load_config(config_path)

            self.assertEqual(
                config["additional_mods_import_path"],
                str(config_path.parent / "extra-imports"),
            )

    def test_invalid_additional_import_list_raises_exporter_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            write_config(config_path, {"additional_mods_import": "*"})

            with self.assertRaisesRegex(
                ExporterError,
                "additional_mods_import",
            ):
                load_config(config_path)

    def test_invalid_additional_import_list_item_raises_exporter_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            write_config(config_path, {"additional_mods_import": ["*", 42]})

            with self.assertRaisesRegex(
                ExporterError,
                "additional_mods_import",
            ):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main()
