import os
import re
import unicodedata
from pathlib import Path

from et.domain.errors import ExporterError
from et.domain.models import Mod, ModMatchCandidates, ModMatches, PakIndex


def normalize_pak_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def build_pak_index(mo2_mods_root: Path) -> PakIndex:
    if not mo2_mods_root.exists():
        raise ExporterError(f"MO2 mods path not found: {mo2_mods_root}")

    pak_index: PakIndex = {}
    for dirpath, _, filenames in os.walk(mo2_mods_root):
        for filename in filenames:
            if filename.lower().endswith(".pak"):
                key = Path(filename).stem.lower()
                pak_index.setdefault(key, []).append(Path(dirpath) / filename)
    return pak_index


def find_mod_matches(
    mods: list[Mod], pak_index: PakIndex, exclusions: list[str]
) -> tuple[ModMatches, ModMatchCandidates, list[Mod], list[Mod]]:
    exclusions_lower = {exclusion.lower() for exclusion in exclusions}
    normalized_pak_index: PakIndex = {}
    for key, paths in pak_index.items():
        normalized_key = normalize_pak_key(key)
        if normalized_key:
            normalized_pak_index.setdefault(normalized_key, []).extend(paths)

    matched: ModMatches = []
    candidates: ModMatchCandidates = []
    missing: list[Mod] = []
    excluded: list[Mod] = []

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
            continue

        candidate_paths: list[Path] = []
        for lookup_value in (name, folder):
            normalized_lookup_key = normalize_pak_key(lookup_value)
            if normalized_lookup_key:
                candidate_paths.extend(
                    normalized_pak_index.get(normalized_lookup_key, [])
                )

        unique_candidate_paths = list(dict.fromkeys(candidate_paths))
        if unique_candidate_paths:
            candidates.append((mod, unique_candidate_paths))
        else:
            missing.append(mod)

    return matched, candidates, missing, excluded
