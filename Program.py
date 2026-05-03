import argparse
import json
import os
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET


class ExporterError(Exception):
    """Domain-specific error for the exporter."""


class LogLevel(Enum):
    """Log level enumeration."""
    SILENT = 0
    ERROR = 1
    WARNING = 2
    VERBOSE = 3


class Logger:
    """Simple logger that respects log level settings."""
    
    def __init__(self, level: LogLevel = LogLevel.WARNING):
        self.level = level
    
    def error(self, message: str) -> None:
        """Log error messages."""
        if self.level.value >= LogLevel.ERROR.value:
            print(f"Error: {message}", file=sys.stderr)
    
    def warning(self, message: str) -> None:
        """Log warning messages."""
        if self.level.value >= LogLevel.WARNING.value:
            print(f"Warning: {message}", file=sys.stderr)
    
    def info(self, message: str) -> None:
        """Log info messages (verbose only)."""
        if self.level.value >= LogLevel.VERBOSE.value:
            print(message)
    
    def log(self, message: str) -> None:
        """Log general messages (verbose only)."""
        if self.level.value >= LogLevel.VERBOSE.value:
            print(message)


# Global logger instance (will be initialized after config load)
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = Logger(LogLevel.WARNING)
    return _logger


def prompt_yes_no(message: str) -> bool:
    """Prompt the user with a yes/no question and return True for yes."""
    while True:
        response = input(f"{message} [y/n]: ").strip().lower()
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")


def prompt_choice(message: str, options: List[str]) -> str:
    """Prompt the user to select a value from the provided options."""
    options_map = {str(index + 1): option for index, option in enumerate(options)}
    print(message)
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")

    while True:
        selection = input("Enter the number of the desired option: ").strip()
        if selection in options_map:
            return options_map[selection]
        print("Invalid selection. Please choose one of the listed numbers.")


def load_config(config_path: Path) -> Dict:
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
    ]
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ExporterError(
            f"Configuration missing required keys: {', '.join(missing)}"
        )

    # Initialize logger with config log level
    global _logger
    log_level_str = config.get("log_level", "Warning").lower()
    log_level_map = {
        "silent": LogLevel.SILENT,
        "error": LogLevel.ERROR,
        "warning": LogLevel.WARNING,
        "verbose": LogLevel.VERBOSE,
    }
    log_level = log_level_map.get(log_level_str, LogLevel.WARNING)
    _logger = Logger(log_level)

    # Ensure exclusions are defined in config. Default to GustavDev per request.
    # Exclusions should be a list of mod names or folder names to ignore when copying.
    if "exclusions" not in config or not isinstance(config.get("exclusions"), list):
        config["exclusions"] = ["GustavDev"]

    return config


def resolve_profile(config: Dict) -> Path:
    profiles_root = Path(config["mo2_profiles_path"]).expanduser()
    if not profiles_root.exists():
        raise ExporterError(f"MO2 profiles path not found: {profiles_root}")

    default_profile = config.get("default_profile")
    if default_profile:
        profile_path = profiles_root / default_profile
        if not profile_path.exists():
            raise ExporterError(
                f"Default profile '{default_profile}' not found in {profiles_root}"
            )
        logger = get_logger()
        logger.info(f"Using default profile: {default_profile}")
        return profile_path

    available_profiles = sorted(
        [
            path.name
            for path in profiles_root.iterdir()
            if path.is_dir() and (path / "modsettings.lsx").exists()
        ]
    )

    if not available_profiles:
        raise ExporterError("No profiles with modsettings.lsx found.")

    selected_name = prompt_choice(
        "Select the target MO2 profile to export:", available_profiles
    )
    logger = get_logger()
    logger.info(f"Selected profile: {selected_name}")
    return profiles_root / selected_name


def parse_modsettings(modsettings_path: Path) -> List[Dict[str, str]]:
    if not modsettings_path.exists():
        raise ExporterError(f"modsettings.lsx not found: {modsettings_path}")

    try:
        tree = ET.parse(modsettings_path)
    except ET.ParseError as error:
        raise ExporterError(f"Failed to parse modsettings.lsx: {error}") from error

    root = tree.getroot()
    mods_parent = root.find(".//node[@id='Mods']/children")
    if mods_parent is None:
        raise ExporterError("Could not locate Mods section in modsettings.lsx.")

    mods: List[Dict[str, str]] = []
    for module_node in mods_parent.findall("node"):
        attributes = {attr.get("id"): attr.get("value") for attr in module_node}
        name = attributes.get("Name")
        uuid = attributes.get("UUID")
        folder = attributes.get("Folder", "")

        if not name or not uuid:
            logger = get_logger()
            logger.warning(
                f"Skipping module missing Name or UUID in modsettings: "
                f"{ET.tostring(module_node, encoding='unicode').strip()}"
            )
            continue

        mods.append({"Name": name, "UUID": uuid, "Folder": folder})

    if not mods:
        raise ExporterError("No valid mods were found in modsettings.lsx.")

    return mods


def ensure_orders_path(orders_root: Path) -> None:
    if not orders_root.exists():
        logger = get_logger()
        logger.info(f"Creating BG3MM orders directory: {orders_root}")
        orders_root.mkdir(parents=True, exist_ok=True)


def write_bg3mm_order(order_path: Path, mods: List[Dict[str, str]]) -> None:
    order_data = {"Order": [{"UUID": mod["UUID"], "Name": mod["Name"]} for mod in mods]}
    with order_path.open("w", encoding="utf-8") as handle:
        json.dump(order_data, handle, indent=2)
    logger = get_logger()
    logger.info(f"BG3MM order file written to: {order_path}")


def build_pak_index(mo2_mods_root: Path) -> Dict[str, List[Path]]:
    if not mo2_mods_root.exists():
        raise ExporterError(f"MO2 mods path not found: {mo2_mods_root}")

    pak_index: Dict[str, List[Path]] = {}
    for dirpath, _, filenames in os.walk(mo2_mods_root):
        for filename in filenames:
            if filename.lower().endswith(".pak"):
                key = Path(filename).stem.lower()
                pak_index.setdefault(key, []).append(Path(dirpath) / filename)
    return pak_index


def find_mod_matches(
    mods: List[Dict[str, str]], pak_index: Dict[str, List[Path]], exclusions: List[str]
) -> Tuple[List[Tuple[Dict[str, str], List[Path]]], List[Dict[str, str]], List[Dict[str, str]]]:
    """Find .pak matches for mods and separate them into matched, missing, and excluded lists.

    Returns a tuple: (matched, missing, excluded)
    - matched: list of tuples (mod, [Path, ...]) for mods with one or more pak files
    - missing: list of mod dicts that had no pak matches
    - excluded: list of mod dicts that were excluded per config
    """
    logger = get_logger()
    exclusions_lower = {ex.lower() for ex in exclusions}

    matched: List[Tuple[Dict[str, str], List[Path]]] = []
    missing: List[Dict[str, str]] = []
    excluded: List[Dict[str, str]] = []

    for mod in mods:
        name = mod.get("Name", "").strip()
        folder = mod.get("Folder", "").strip()

        if name.lower() in exclusions_lower or folder.lower() in exclusions_lower:
            excluded.append(mod)
            continue

        lookup_key = name.lower()
        matches = pak_index.get(lookup_key, [])
        if not matches and folder:
            matches = pak_index.get(folder.lower(), [])

        if matches:
            matched.append((mod, matches))
        else:
            missing.append(mod)

    logger.info(f"Found {len(matched)} mod(s) with pak files, {len(missing)} missing, {len(excluded)} excluded.")
    return matched, missing, excluded


def copy_mods_from_matches(
    mods_with_matches: List[Tuple[Dict[str, str], List[Path]]],
    destination_root: Path,
):
    """Copy .pak files based on precomputed matches. Prompts for overwrite handling.

    `mods_with_matches` is a list of tuples (mod_dict, [Path, ...]).
    """
    logger = get_logger()

    if not destination_root.exists():
        logger.info(f"Creating BG3 native mods directory: {destination_root}")
        destination_root.mkdir(parents=True, exist_ok=True)

    overwrite_mode: Optional[str] = None  # 'overwrite' or 'skip'

    files_to_copy: List[Tuple[Path, Path]] = []
    skipped_files: List[Path] = []

    for mod, matches in mods_with_matches:
        for source_path in matches:
            destination_path = destination_root / source_path.name
            if destination_path.exists():
                decision = overwrite_mode
                if decision is None:
                    decision = prompt_overwrite(destination_path)
                    if decision == "overwrite_all":
                        overwrite_mode = "overwrite"
                        decision = "overwrite"
                    elif decision == "skip_all":
                        overwrite_mode = "skip"
                        decision = "skip"

                if decision == "skip":
                    skipped_files.append(destination_path)
                    continue

                files_to_copy.append((source_path, destination_path))
            else:
                files_to_copy.append((source_path, destination_path))

    total_files = len(files_to_copy)
    if total_files == 0:
        logger.info("No files to copy.")
        return

    logger.info(f"Copying {total_files} file(s)...")
    for idx, (source_path, destination_path) in enumerate(files_to_copy, 1):
        progress = int((idx / total_files) * 100)
        bar_length = 40
        filled = int(bar_length * idx / total_files)
        bar = "=" * filled + "-" * (bar_length - filled)

        print(f"\r[{bar}] {progress}% ({idx}/{total_files}) {source_path.name[:50]}", end="", flush=True)

        shutil.copy2(source_path, destination_path)

    print()

    if skipped_files:
        logger.info(f"Skipped {len(skipped_files)} existing file(s).")


def copy_mods(
    mods: List[Dict[str, str]],
    pak_index: Dict[str, List[Path]],
    destination_root: Path,
) -> None:
    logger = get_logger()
    
    if not destination_root.exists():
        logger.info(f"Creating BG3 native mods directory: {destination_root}")
        destination_root.mkdir(parents=True, exist_ok=True)

    overwrite_mode: Optional[str] = None  # 'overwrite' or 'skip'
    
    # Collect all files to copy first for progress tracking
    files_to_copy: List[Tuple[Path, Path]] = []
    skipped_files: List[Path] = []
    
    for mod in mods:
        lookup_key = mod["Name"].lower()
        matches = pak_index.get(lookup_key, [])
        if not matches and mod["Folder"]:
            lookup_key = mod["Folder"].lower()
            matches = pak_index.get(lookup_key, [])

        if not matches:
            logger.warning(f"No .pak files found for mod '{mod['Name']}'.")
            continue

        for source_path in matches:
            destination_path = destination_root / source_path.name
            if destination_path.exists():
                decision = overwrite_mode
                if decision is None:
                    decision = prompt_overwrite(destination_path)
                    if decision == "overwrite_all":
                        overwrite_mode = "overwrite"
                        decision = "overwrite"
                    elif decision == "skip_all":
                        overwrite_mode = "skip"
                        decision = "skip"

                if decision == "skip":
                    skipped_files.append(destination_path)
                    continue

                files_to_copy.append((source_path, destination_path))
            else:
                files_to_copy.append((source_path, destination_path))
    
    # Copy files with progress bar
    total_files = len(files_to_copy)
    if total_files == 0:
        logger.info("No files to copy.")
        return
    
    # Simple progress bar implementation
    logger.info(f"Copying {total_files} file(s)...")
    for idx, (source_path, destination_path) in enumerate(files_to_copy, 1):
        # Calculate progress percentage
        progress = int((idx / total_files) * 100)
        bar_length = 40
        filled = int(bar_length * idx / total_files)
        bar = "=" * filled + "-" * (bar_length - filled)
        
        # Print progress bar on same line
        print(f"\r[{bar}] {progress}% ({idx}/{total_files}) {source_path.name[:50]}", end="", flush=True)
        
        shutil.copy2(source_path, destination_path)
    
    # Print newline after progress bar
    print()
    
    if skipped_files:
        logger.info(f"Skipped {len(skipped_files)} existing file(s).")


def prompt_overwrite(existing_path: Path) -> str:
    """Prompt user for duplicate file handling with numbered options."""
    options = [
        "Rewrite",
        "Keep existing",
        "Rewrite Always",
        "Keep Always",
    ]
    message = f"File already exists at '{existing_path}'. Choose an option:"
    selected = prompt_choice(message, options)
    
    if selected == "Rewrite":
        return "overwrite"
    elif selected == "Keep existing":
        return "skip"
    elif selected == "Rewrite Always":
        return "overwrite_all"
    elif selected == "Keep Always":
        return "skip_all"
    else:
        return "skip"  # Default to skip


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Mod Organizer 2 profile to BG3 Mod Manager format."
    )
    parser.add_argument(
        "--config",
        required=False,
        type=Path,
        help="Path to configuration JSON file.",
    )
    args = parser.parse_args()

    if not prompt_yes_no("Do you want to start the MO2 → BG3MM export process?"):
        logger = get_logger()
        logger.info("Export aborted by user.")
        return

    if args.config is None:
        raise ExporterError("No configuration file specified. Use --config <path>.")

    config = load_config(args.config)
    profile_path = resolve_profile(config)
    profile_name = profile_path.name
    modsettings_path = profile_path / "modsettings.lsx"
    mods = parse_modsettings(modsettings_path)

    orders_root = Path(config["bg3mm_orders_path"]).expanduser()
    ensure_orders_path(orders_root)
    order_path = orders_root / f"{profile_name}.json"

    logger = get_logger()
    
    if order_path.exists():
        if not prompt_yes_no(
            f"BG3MM order '{order_path.name}' already exists. Overwrite?"
        ):
            logger.info("Existing BG3MM order kept. Export halted.")
            return

    write_bg3mm_order(order_path, mods)
    logger.info(f"BG3MM order file created for profile '{profile_name}'.")

    if not prompt_yes_no(
        "Would you like to import MO2 mods into the game's native Mods folder?"
    ):
        logger = get_logger()
        logger.info("Order export complete. Mod file import skipped.")
        return

    destination_root = Path(config["bg3_native_mods_path"]).expanduser()
    
    # Prompt to clean native mods folder
    if destination_root.exists() and any(destination_root.iterdir()):
        if prompt_yes_no(
            "Do you want to clean the native mods folder before copying new mods?"
        ):
            logger = get_logger()
            logger.info(f"Cleaning native mods folder: {destination_root}")
            for item in destination_root.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info("Native mods folder cleaned.")

    pak_index = build_pak_index(Path(config["mo2_mods_path"]).expanduser())
    # Pre-copy check: find which mods have pak files, which are missing, and which are excluded.
    matched, missing, excluded = find_mod_matches(mods, pak_index, config.get("exclusions", []))

    if excluded:
        logger.info(f"{len(excluded)} mod(s) are excluded and will be skipped: {', '.join(m.get('Name','<unknown>') for m in excluded)}")

    if missing:
        print("The following mods were listed in the profile but no .pak files were found:")
        for m in missing:
            print(f" - {m.get('Name','<unknown>')} (Folder: {m.get('Folder','')})")

        if not prompt_yes_no("Proceed with copying the available mods anyway?"):
            logger.info("User chose not to proceed after missing-mods check. Export halted.")
            return

    # Perform copying for matched mods only
    copy_mods_from_matches(matched, destination_root)

    logger = get_logger()
    logger.info("Export and import operations completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except ExporterError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

