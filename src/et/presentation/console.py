import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, TypeVar

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table


T = TypeVar("T")


class LogLevel(Enum):
    """Log level enumeration."""

    SILENT = 0
    ERROR = 1
    WARNING = 2
    VERBOSE = 3


class Logger:
    """Rich-backed logger that respects log level settings."""

    def __init__(
        self,
        level: LogLevel = LogLevel.WARNING,
        console: Optional[Console] = None,
        error_console: Optional[Console] = None,
    ):
        self.level = level
        self.console = console or Console()
        self.error_console = error_console or Console(stderr=True)

    def error(self, message: str) -> None:
        if self.level.value >= LogLevel.ERROR.value:
            self.error_console.print(f"[bold red]Error:[/bold red] {message}")

    def warning(self, message: str) -> None:
        if self.level.value >= LogLevel.WARNING.value:
            self.error_console.print(f"[yellow]Warning:[/yellow] {message}")

    def missing_module_properties_warning(
        self, info: dict[str, str], raw_info: str
    ) -> None:
        if self.level.value < LogLevel.WARNING.value:
            return

        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value")

        for key, value in info.items():
            table.add_row(key, value)

        self.error_console.print()
        self.error_console.print(
            "[yellow]Module with missing 'Name' or 'UUID' properties in "
            "modsettings was detected.[/yellow]"
        )
        self.error_console.print("[bold]Info:[/bold]")
        self.error_console.print(table)
        self.error_console.print("[bold]Raw info:[/bold]")
        self.error_console.print(
            Syntax(raw_info, "xml", theme="ansi_dark", word_wrap=True)
        )

    def info(self, message: str) -> None:
        if self.level.value >= LogLevel.VERBOSE.value:
            self.console.print(message)

    def log(self, message: str) -> None:
        if self.level.value >= LogLevel.VERBOSE.value:
            self.console.print(message)


_logger: Optional[Logger] = None
_console = Console()


def configure_logger(level: LogLevel) -> Logger:
    global _logger
    _logger = Logger(level)
    return _logger


def get_logger() -> Logger:
    global _logger
    if _logger is None:
        _logger = Logger(LogLevel.WARNING)
    return _logger


def parse_log_level(value: str) -> LogLevel:
    log_level_map = {
        "silent": LogLevel.SILENT,
        "error": LogLevel.ERROR,
        "warning": LogLevel.WARNING,
        "verbose": LogLevel.VERBOSE,
    }
    return log_level_map.get(value.lower(), LogLevel.WARNING)


def prompt_yes_no(message: str) -> bool:
    return Confirm.ask(message, console=_console)


def prompt_choice(message: str, options: Iterable[T]) -> T:
    options_list = list(options)
    if not options_list:
        raise ValueError("Options must not be empty.")

    _console.print(message)
    for index, option in enumerate(options_list, start=1):
        _console.print(f"  [cyan]{index}[/cyan]. {option}")

    valid_choices = [str(index) for index in range(1, len(options_list) + 1)]
    selection = Prompt.ask(
        "Enter your choice",
        choices=valid_choices,
        console=_console,
    )
    return options_list[int(selection) - 1]


def print_missing_mods(mods: Iterable[dict[str, str]]) -> None:
    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Name", style="cyan")
    table.add_column("Folder")

    has_rows = False
    for mod in mods:
        has_rows = True
        table.add_row(
            mod.get("Name", "<unknown>"),
            mod.get("Folder", "") or "<missing>",
        )

    if not has_rows:
        return

    _console.print(
        "[yellow]The following mods were listed in the profile but no .pak files were found:[/yellow]"
    )
    _console.print(table)


def prompt_pak_match_confirmation(
    mod: dict[str, str], candidate_paths: list[Path]
) -> list[Path]:
    _console.print()
    _console.print(f"[bold]Folder:[/bold] {mod.get('Folder', '') or '<missing>'}")

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Declared name", style="cyan")
    table.add_column("Actual name")
    for candidate_path in candidate_paths:
        table.add_row(mod.get("Name", "<unknown>"), candidate_path.stem)
    _console.print(table)

    options: list[str] = []
    option_paths: dict[str, list[Path]] = {}
    if len(candidate_paths) > 1:
        label = "Use all available files"
        options.append(label)
        option_paths[label] = candidate_paths
    for candidate_path in candidate_paths:
        label = f"Use available file ({candidate_path.name})"
        options.append(label)
        option_paths[label] = [candidate_path]

    ignore_label = "Ignore this mod"
    options.append(ignore_label)
    option_paths[ignore_label] = []

    selected = prompt_choice(
        "What to do:",
        options,
    )
    return option_paths[selected]


def copy_with_progress(files_to_copy: list[tuple[Path, Path]]) -> None:
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=_console,
    )

    with progress:
        task = progress.add_task("Copying mods", total=len(files_to_copy))
        for source_path, destination_path in files_to_copy:
            progress.update(task, description=f"Copying {source_path.name[:50]}")
            shutil.copy2(source_path, destination_path)
            progress.advance(task)


def print_error(message: str) -> None:
    Console(stderr=True).print(f"[bold red]Error:[/bold red] {message}")


def print_cancelled() -> None:
    Console(stderr=True).print("\n[yellow]Operation cancelled by user.[/yellow]")


def exit_with_error() -> None:
    sys.exit(1)
