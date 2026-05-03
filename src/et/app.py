import argparse
from pathlib import Path

from et.application.exporter import run_export
from et.domain.errors import ExporterError
from et.presentation.console import exit_with_error, print_cancelled, print_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Mod Organizer 2 profile to BG3 Mod Manager format."
    )
    parser.add_argument(
        "--config",
        required=False,
        type=Path,
        help="Path to configuration JSON file.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_export(args.config)
    except ExporterError as error:
        print_error(str(error))
        exit_with_error()
    except KeyboardInterrupt:
        print_cancelled()
        exit_with_error()
