from pathlib import Path
from typing import Annotated

import typer

from et.application.exporter import run_export
from et.domain.errors import ExporterError
from et.presentation.console import exit_with_error, print_cancelled, print_error


app = typer.Typer(
    invoke_without_command=True,
    help="Export Mod Organizer 2 profiles to BG3 Mod Manager format.",
)


@app.callback(invoke_without_command=True)
def cli(ctx: typer.Context) -> None:
    """Export Mod Organizer 2 profiles to BG3 Mod Manager format."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def init_session(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration JSON file.",
        ),
    ] = Path("config.json"),
) -> None:
    try:
        run_export(config)
    except ExporterError as error:
        print_error(str(error))
        exit_with_error()
    except KeyboardInterrupt:
        print_cancelled()
        exit_with_error()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
