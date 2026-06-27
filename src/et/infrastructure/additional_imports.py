from pathlib import Path
from typing import Optional

from et.domain.errors import ExporterError
from et.presentation.console import copy_with_progress, get_logger

from .copying import prompt_overwrite


def _normalize_entry(value: str) -> str:
    return Path(value).name.lower()


def _scan_pak_files(
    source_root: Path,
) -> tuple[list[Path], dict[str, Path], dict[str, list[Path]]]:
    unique_files: list[Path] = []
    files_by_key: dict[str, Path] = {}
    duplicate_paths_by_name: dict[str, list[Path]] = {}

    for source_path in sorted(source_root.rglob("*.pak"), key=lambda path: str(path).lower()):
        name_key = source_path.name.lower()
        if name_key in files_by_key:
            duplicate_paths_by_name.setdefault(name_key, [files_by_key[name_key]]).append(
                source_path
            )
            continue

        unique_files.append(source_path)
        keys = {
            name_key,
            source_path.stem.lower(),
        }
        for key in keys:
            if key in files_by_key:
                continue
            files_by_key[key] = source_path

    return unique_files, files_by_key, duplicate_paths_by_name


def _warn_about_duplicates(duplicate_paths_by_name: dict[str, list[Path]]) -> None:
    logger = get_logger()
    for key, paths in duplicate_paths_by_name.items():
        logger.warning(
            "Duplicate additional mod import entry "
            f"'{key}' found. Using '{paths[0]}' and ignoring "
            f"{len(paths) - 1} duplicate path(s)."
        )


def resolve_additional_mod_files(
    source_root: Path,
    import_entries: list[str],
) -> tuple[list[Path], list[str]]:
    if not source_root.exists():
        raise ExporterError(f"Additional mods import path not found: {source_root}")
    if not source_root.is_dir():
        raise ExporterError(
            f"Additional mods import path is not a directory: {source_root}"
        )

    all_files, files_by_key, duplicate_paths_by_name = _scan_pak_files(source_root)
    _warn_about_duplicates(duplicate_paths_by_name)

    if "*" in import_entries:
        return all_files, []

    selected_files: list[Path] = []
    selected_keys: set[str] = set()
    missing_entries: list[str] = []

    for entry in import_entries:
        key = _normalize_entry(entry)
        source_path = files_by_key.get(key)
        if source_path is None:
            missing_entries.append(entry)
            continue
        if str(source_path).lower() in selected_keys:
            continue
        selected_files.append(source_path)
        selected_keys.add(str(source_path).lower())

    return selected_files, missing_entries


def copy_additional_mods(
    source_root: Path,
    destination_root: Path,
    import_entries: list[str],
) -> None:
    logger = get_logger()
    selected_files, missing_entries = resolve_additional_mod_files(
        source_root,
        import_entries,
    )

    if missing_entries:
        logger.warning(
            "Additional import mod(s) not found and will be skipped: "
            f"{', '.join(missing_entries)}"
        )

    if not selected_files:
        logger.info("No additional mod files to copy.")
        return

    destination_root.mkdir(parents=True, exist_ok=True)
    overwrite_mode: Optional[str] = None
    files_to_copy: list[tuple[Path, Path]] = []
    skipped_files: list[Path] = []

    for source_path in selected_files:
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

    if not files_to_copy:
        logger.info("No additional mod files to copy.")
        return

    logger.info(f"Copying {len(files_to_copy)} additional mod file(s)...")
    copy_with_progress(files_to_copy)

    if skipped_files:
        logger.info(f"Skipped {len(skipped_files)} existing additional mod file(s).")
