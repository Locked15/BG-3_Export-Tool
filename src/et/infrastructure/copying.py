import shutil
from pathlib import Path
from typing import Optional

from et.domain.models import ModMatches
from et.presentation.console import copy_with_progress, get_logger, prompt_choice


def prompt_overwrite(existing_path: Path) -> str:
    options = [
        "Rewrite",
        "Keep existing",
        "Rewrite Always",
        "Keep Always",
    ]
    selected = prompt_choice(
        f"File already exists at '{existing_path}'. Choose an option:", options
    )

    if selected == "Rewrite":
        return "overwrite"
    if selected == "Keep existing":
        return "skip"
    if selected == "Rewrite Always":
        return "overwrite_all"
    if selected == "Keep Always":
        return "skip_all"
    return "skip"


def clean_native_mods_folder(destination_root: Path) -> None:
    logger = get_logger()
    logger.info(f"Cleaning native mods folder: {destination_root}")
    for item in destination_root.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    logger.info("Native mods folder cleaned.")


def copy_mods_from_matches(
    mods_with_matches: ModMatches,
    destination_root: Path,
) -> None:
    logger = get_logger()

    if not destination_root.exists():
        logger.info(f"Creating BG3 native mods directory: {destination_root}")
        destination_root.mkdir(parents=True, exist_ok=True)

    overwrite_mode: Optional[str] = None
    files_to_copy: list[tuple[Path, Path]] = []
    skipped_files: list[Path] = []

    for _, matches in mods_with_matches:
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

    if not files_to_copy:
        logger.info("No files to copy.")
        return

    logger.info(f"Copying {len(files_to_copy)} file(s)...")
    copy_with_progress(files_to_copy)

    if skipped_files:
        logger.info(f"Skipped {len(skipped_files)} existing file(s).")
