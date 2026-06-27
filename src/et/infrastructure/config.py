import json
from pathlib import Path
from typing import Any

from et.domain.errors import ExporterError
from et.presentation.console import configure_logger, parse_log_level


Config = dict[str, Any]


def load_config(config_path: Path) -> Config:
    if not config_path:
        raise ExporterError("Configuration file path must be provided.")
    if not config_path.exists():
        raise ExporterError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except json.JSONDecodeError as error:
        raise ExporterError(f"Failed to parse configuration file: {error}") from error

    required_keys = [
        "mo2_profiles_path",
        "mo2_mods_path",
        "bg3mm_orders_path",
        "bg3_native_mods_path",
        "configurations_source_path",
        "configurations_destination_path",
    ]
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ExporterError(
            f"Configuration missing required keys: {', '.join(missing)}"
        )

    configure_logger(parse_log_level(config.get("log_level", "Warning")))

    if "exclusions" not in config or not isinstance(config.get("exclusions"), list):
        config["exclusions"] = ["GustavDev"]

    additional_imports = config.get("additional_mods_import", [])
    if not isinstance(additional_imports, list) or not all(
        isinstance(entry, str) for entry in additional_imports
    ):
        raise ExporterError(
            "Configuration key 'additional_mods_import' must be a list of strings."
        )
    config["additional_mods_import"] = additional_imports

    additional_import_path = config.get("additional_mods_import_path", "import")
    if not isinstance(additional_import_path, str):
        raise ExporterError(
            "Configuration key 'additional_mods_import_path' must be a string."
        )

    source_path = Path(additional_import_path).expanduser()
    if not source_path.is_absolute():
        source_path = config_path.parent / source_path
    config["additional_mods_import_path"] = str(source_path)

    return config
