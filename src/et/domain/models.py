from pathlib import Path

Mod = dict[str, str]
PakIndex = dict[str, list[Path]]
ModMatches = list[tuple[Mod, list[Path]]]
ModMatchCandidates = list[tuple[Mod, list[Path]]]
