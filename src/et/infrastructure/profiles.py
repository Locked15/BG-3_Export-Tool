from pathlib import Path

from et.domain.errors import ExporterError
from et.infrastructure.config import Config
from et.presentation.console import get_logger, prompt_choice


def resolve_profile(config: Config) -> Path:
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
        get_logger().info(f"Using default profile: {default_profile}")
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
    get_logger().info(f"Selected profile: {selected_name}")
    return profiles_root / selected_name
