from pathlib import Path

from et.domain.errors import ExporterError
from et.domain.modsettings import parse_modsettings
from et.infrastructure.additional_imports import copy_additional_mods
from et.infrastructure.config import load_config
from et.infrastructure.configurations import copy_configurations
from et.infrastructure.copying import clean_native_mods_folder, copy_mods_from_matches
from et.infrastructure.orders import ensure_orders_path, write_bg3mm_order
from et.infrastructure.pak_index import build_pak_index, find_mod_matches
from et.infrastructure.profiles import resolve_profile
from et.presentation.console import (
    get_logger,
    print_missing_mods,
    prompt_pak_match_confirmation,
    prompt_yes_no,
)


def run_export(config_path: Path) -> None:
    if not prompt_yes_no("Do you want to start the MO2 -> BG3MM export process?"):
        get_logger().info("Export aborted by user.")
        return

    if config_path is None:
        raise ExporterError("No configuration file specified. Use --config <path>.")

    config = load_config(config_path)
    profile_path = resolve_profile(config)
    profile_name = profile_path.name
    mods = parse_modsettings(profile_path / "modsettings.lsx")

    orders_root = Path(config["bg3mm_orders_path"]).expanduser()
    ensure_orders_path(orders_root)
    order_path = orders_root / f"{profile_name}.json"

    logger = get_logger()
    if order_path.exists():
        if not prompt_yes_no(f"BG3MM order '{order_path.name}' already exists. Overwrite?"):
            logger.info("Existing BG3MM order kept. Export halted.")
            return

    write_bg3mm_order(order_path, mods)
    logger.info(f"BG3MM order file created for profile '{profile_name}'.")

    if prompt_yes_no(
        "Would you like to import MO2 mods into the game's native Mods folder?"
    ):
        destination_root = Path(config["bg3_native_mods_path"]).expanduser()
        if destination_root.exists() and any(destination_root.iterdir()):
            if prompt_yes_no(
                "Do you want to clean the native mods folder before copying new mods?"
            ):
                clean_native_mods_folder(destination_root)

        pak_index = build_pak_index(Path(config["mo2_mods_path"]).expanduser())
        matched, candidates, missing, excluded = find_mod_matches(
            mods, pak_index, config.get("exclusions", [])
        )

        if excluded:
            logger.info(
                f"{len(excluded)} mod(s) are excluded and will be skipped: "
                f"{', '.join(mod.get('Name', '<unknown>') for mod in excluded)}"
            )

        for candidate_mod, candidate_paths in candidates:
            confirmed_paths = prompt_pak_match_confirmation(candidate_mod, candidate_paths)
            if confirmed_paths:
                matched.append((candidate_mod, confirmed_paths))
            else:
                missing.append(candidate_mod)

        if missing:
            print_missing_mods(missing)
            if not prompt_yes_no("Proceed with copying the available mods anyway?"):
                logger.info(
                    "User chose not to proceed after missing-mods check. Mod import skipped."
                )
            else:
                copy_mods_from_matches(matched, destination_root)
        else:
            copy_mods_from_matches(matched, destination_root)
    else:
        logger.info("Mod file import skipped.")

    if prompt_yes_no("Would you like to copy Script Extender configuration files?"):
        copy_configurations(
            Path(config["configurations_source_path"]).expanduser(),
            Path(config["configurations_destination_path"]).expanduser(),
        )
    else:
        logger.info("Configuration copy skipped.")

    additional_imports = config.get("additional_mods_import", [])
    if additional_imports:
        if prompt_yes_no(
            "Would you like to import additional mods from the configured import folder?"
        ):
            copy_additional_mods(
                Path(config["additional_mods_import_path"]).expanduser(),
                Path(config["bg3_native_mods_path"]).expanduser(),
                additional_imports,
            )
        else:
            logger.info("Additional mod import skipped.")
    else:
        logger.info("No additional mod imports configured.")

    logger.info("Export and import operations completed successfully.")
