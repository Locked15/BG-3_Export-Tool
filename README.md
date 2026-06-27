# BG3 MO2 Exporter

Exports a Mod Organizer 2 Baldur's Gate 3 profile to a BG3 Mod Manager order
file and can copy matching `.pak` files into the native BG3 Mods folder.

The exporter can also copy additional `.pak` files from a configured import
folder after the overwrite/configuration copy step. Add `.pak` files to the
local `import/` directory or point `additional_mods_import_path` at another
folder, then configure `additional_mods_import` with filenames, stems, or `"*"`
to copy every `.pak` found recursively.

## Usage

```powershell
uv run -m et.app
uv run -m et.app init-session
uv run -m et.app init-session --config config.json
```

Legacy compatibility is still available:

```powershell
uv run et-export --config config.json
```

## Structure

```text
src/et/app.py                  CLI entry point
src/et/application/            Export workflow orchestration
src/et/domain/                 Exporter errors, mod models, modsettings parsing
src/et/infrastructure/         Config, profiles, orders, pak index, file copying
src/et/presentation/           Rich console, prompts, progress output
```
