from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from et.domain.errors import ExporterError
from et.domain.models import Mod
from et.presentation.console import get_logger


def _describe_module(attributes: Optional[Mod]) -> str:
    if attributes is None:
        return "<none>"

    module_name = attributes.get("Name") or "<missing>"
    module_uuid = attributes.get("UUID") or "<missing>"
    module_folder = attributes.get("Folder") or "<missing>"
    return f"{module_name} (Folder: {module_folder}, UUID: {module_uuid})"


def _nearest_valid_module(
    module_attributes: list[Mod], start: int, step: int
) -> Optional[Mod]:
    index = start
    while 0 <= index < len(module_attributes):
        attributes = module_attributes[index]
        if attributes.get("Name") and attributes.get("UUID"):
            return attributes
        index += step
    return None


def parse_modsettings(modsettings_path: Path) -> list[Mod]:
    if not modsettings_path.exists():
        raise ExporterError(f"modsettings.lsx not found: {modsettings_path}")

    try:
        tree = ET.parse(modsettings_path)
    except ET.ParseError as error:
        raise ExporterError(f"Failed to parse modsettings.lsx: {error}") from error

    root = tree.getroot()
    mods_parent = root.find(".//node[@id='Mods']/children")
    if mods_parent is None:
        raise ExporterError("Could not locate Mods section in modsettings.lsx.")

    module_nodes = mods_parent.findall("node")
    module_attributes: list[Mod] = [
        {attr.get("id"): attr.get("value") for attr in module_node}
        for module_node in module_nodes
    ]

    mods: list[Mod] = []
    for index, (module_node, attributes) in enumerate(
        zip(module_nodes, module_attributes), start=1
    ):
        name = attributes.get("Name")
        uuid = attributes.get("UUID")
        folder = attributes.get("Folder", "")

        if not name or not uuid:
            previous_module = _nearest_valid_module(module_attributes, index - 2, -1)
            next_module = _nearest_valid_module(module_attributes, index, 1)
            get_logger().missing_module_properties_warning(
                {
                    "Load order entry": f"{index} of {len(module_nodes)}",
                    "Problem entry Folder": folder or "<missing>",
                    "Previous valid mod": _describe_module(previous_module),
                    "Next valid mod": _describe_module(next_module),
                    "Note": (
                        "Exact mod directory cannot be detected because this entry "
                        "has no Name, UUID, or Folder."
                    ),
                },
                ET.tostring(module_node, encoding="unicode").strip(),
            )
            continue

        mods.append({"Name": name, "UUID": uuid, "Folder": folder})

    if not mods:
        raise ExporterError("No valid mods were found in modsettings.lsx.")

    return mods
