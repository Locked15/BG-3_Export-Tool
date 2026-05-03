from pathlib import Path

from et.domain.errors import ExporterError
from et.presentation.console import copy_with_progress, get_logger, prompt_choice


def _collect_files(source_root: Path, destination_root: Path) -> list[tuple[Path, Path]]:
    files_to_copy: list[tuple[Path, Path]] = []
    for source_path in source_root.rglob("*"):
        if source_path.is_file():
            destination_path = destination_root / source_path.relative_to(source_root)
            files_to_copy.append((source_path, destination_path))
    return files_to_copy


def _resolve_conflicts(files_to_copy: list[tuple[Path, Path]]) -> list[tuple[Path, Path]]:
    resolved_files: list[tuple[Path, Path]] = []

    for source_path, destination_path in files_to_copy:
        if destination_path.exists():
            selected = prompt_choice(
                f"Configuration file already exists at '{destination_path}'. Choose an option:",
                ["Overwrite", "Ignore"],
            )
            if selected == "Ignore":
                continue

        resolved_files.append((source_path, destination_path))

    return resolved_files


def copy_configurations(source_root: Path, destination_root: Path) -> None:
    logger = get_logger()

    if not source_root.exists():
        raise ExporterError(f"Configurations source path not found: {source_root}")
    if not source_root.is_dir():
        raise ExporterError(f"Configurations source path is not a directory: {source_root}")

    destination_root.mkdir(parents=True, exist_ok=True)

    files_to_copy = _collect_files(source_root, destination_root)
    if not files_to_copy:
        logger.info(f"No configuration files found in: {source_root}")
        return

    files_to_copy = _resolve_conflicts(files_to_copy)
    if not files_to_copy:
        logger.info("No configuration files to copy.")
        return

    for _, destination_path in files_to_copy:
        destination_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Copying {len(files_to_copy)} configuration file(s)...")
    copy_with_progress(files_to_copy)
