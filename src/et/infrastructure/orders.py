import json
from pathlib import Path

from et.domain.models import Mod
from et.presentation.console import get_logger


def ensure_orders_path(orders_root: Path) -> None:
    if not orders_root.exists():
        get_logger().info(f"Creating BG3MM orders directory: {orders_root}")
        orders_root.mkdir(parents=True, exist_ok=True)


def write_bg3mm_order(order_path: Path, mods: list[Mod]) -> None:
    order_data = {"Order": [{"UUID": mod["UUID"], "Name": mod["Name"]} for mod in mods]}
    with order_path.open("w", encoding="utf-8") as handle:
        json.dump(order_data, handle, indent=2)
    get_logger().info(f"BG3MM order file written to: {order_path}")
