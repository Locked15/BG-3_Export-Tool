# BG3 Export Tool (MO2 → BG3MM)

This tool exports a Mod Organizer 2 (MO2) profile into a BG3 Mod Manager (BG3MM) order file and optionally copies `.pak` mod files into the game's native Mods folder.

**Quick Start**
- **Prerequisite:** Install Python 3.8+ (3.10+ recommended).
- **Prepare a config:** Copy `Samples/ET ConfigSample.json` and update the required paths.
- **Run (PowerShell):**
```
cd 'd:\Source\VSC Repos\Python\Gaming\Baldurs Gate 3\ET'
python .\Program.py --config '.\Samples\ET ConfigSample.json'
# or
py -3 .\Program.py --config '.\Samples\ET ConfigSample.json'
```

**Required config keys**
- `mo2_profiles_path`: Path to MO2 profiles folder (each profile contains `modsettings.lsx`).
- `mo2_mods_path`: Path where MO2 stores mod `.pak` files.
- `bg3mm_orders_path`: Destination folder for BG3MM order JSON files.
- `bg3_native_mods_path`: Game's native Mods folder to copy `.pak` files into.

Optional keys:
- `default_profile`: (optional) profile name to skip interactive selection.
- `log_level`: One of `Silent`, `Error`, `Warning`, `Verbose` (default `Warning`).
- `exclusions`: list of mod names or folder names to skip copying (defaults to `["GustavDev"]`).

The sample config is located at `Samples/ET ConfigSample.json`.

**What the script does**
- Reads `modsettings.lsx` from the chosen MO2 profile and extracts enabled mods.
- Writes a BG3MM order file named `<profile>.json` into the `bg3mm_orders_path`.
- Optionally copies matching `.pak` files from `mo2_mods_path` into `bg3_native_mods_path`.

**Interactive prompts**
- Confirm start of export.
- Profile selection (unless `default_profile` is set).
- Confirm overwriting existing BG3MM order files.
- Whether to import `.pak` files into the game's native Mods folder.
- Optionally clean the native Mods folder before copying.
- Overwrite handling for existing `.pak` files: `Rewrite`, `Keep existing`, `Rewrite Always`, `Keep Always`.

**Behavior & notes**
- Paths with spaces must be quoted in the command line.
- The tool uses only the Python standard library; no extra dependencies required.
- If mods are listed in the profile but no `.pak` is found, the tool will list them and ask whether to proceed.
- The BG3MM order file is a JSON file with the profile name as the filename.
- Exit codes: `0` on success, `1` on exporter errors (e.g., missing config keys, parse errors).

**Troubleshooting**
- "Configuration missing required keys": ensure the JSON contains the four required keys above.
- "MO2 profiles path not found": verify `mo2_profiles_path` and that it contains profile folders with `modsettings.lsx`.
- "modsettings.lsx not found": ensure the selected profile folder contains `modsettings.lsx`.
- No `.pak` files found for mods: confirm `mo2_mods_path` points at the folder where MO2 stores `.pak` files.

**Automation / non-interactive runs**
The script is interactive by design. To reduce interaction set `default_profile` in the config to avoid profile selection. The script does not provide a full non-interactive mode (for example, to auto-accept all overwrites). If you want a non-interactive run, I can add CLI flags such as `--yes`, `--overwrite-all`, and `--no-copy` — tell me which behavior you prefer.

**Contribution / Support**
If you'd like changes to the README, extra CLI flags, or logging tweaks, open an issue or request the change here and I can implement it.

--
Generated based on `Program.py` in this repository.
