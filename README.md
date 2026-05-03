# BG3 MO2 Exporter

Exports a Mod Organizer 2 Baldur's Gate 3 profile to a BG3 Mod Manager order
file and can copy matching `.pak` files into the native BG3 Mods folder.

## Usage

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
