import logging
import os
from pathlib import Path
from typing import Optional

import typer
from nemreader import (__version__, nmis_in_file, output_as_csv,
                       output_as_daily_csv, output_as_sqlite)

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
app = typer.Typer()
DEFAULT_DIR = Path(".")


def version_callback(value: bool):
    if value:
        typer.echo(f"nemreader version: {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback
    ),
):
    """nemreader

    Parse AEMO NEM12 and NEM13 meter data files
    """
    pass


@app.command()
def list_nmis(nemfile: Path, verbose: bool = typer.Option(False, "--verbose", "-v")):
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    nmis = list(nmis_in_file(nemfile))
    typer.echo("The following NMI[suffix] exist in this file:")
    for nmi, suffixes in nmis:
        suffix_str = ",".join(suffixes)
        typer.echo(f"{nmi}[{suffix_str}]")


@app.command()
def output_csv(
    nemfile: Path,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    set_interval: Optional[int] = None,
    outdir: Path = typer.Option(
        DEFAULT_DIR,
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
):
    """Output NEM file to transposed CSV.

    NEMFILE is the name of the file to parse.
    """
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    for fname in output_as_csv(nemfile, output_dir=outdir, set_interval=set_interval):
        typer.echo(f"Created {fname}")


@app.command()
def output_csv_daily(
    nemfile: Path,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    outdir: Path = typer.Option(
        DEFAULT_DIR,
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
):
    """Output NEM file to transposed CSV.

    NEMFILE is the name of the file to parse.
    """
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    fname = output_as_daily_csv(nemfile, output_dir=outdir)
    typer.echo(f"Created {fname}")


@app.command()
def output_sqlite(
    nemfile: Path,
    outdir: Path = typer.Option(
        DEFAULT_DIR,
        exists=True,
        file_okay=True,
        dir_okay=True,
        writable=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    five_min: bool = typer.Option(False, "--five-min", "-5"),
):
    """Output NEM file to transposed CSV.

    NEMFILE is the name of the file to parse.
    """
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    if os.path.isdir(nemfile):
        typer.echo(f"Getting files in directory {nemfile}")
        files = list(nemfile.glob("*.csv"))
        files += list(nemfile.glob("*.zip"))
    else:
        files = [nemfile]
    for fp in files:
        typer.echo(f"Processing {fp}")
        try:
            output_as_sqlite(fp, output_dir=outdir, make_fivemins=five_min)
        except Exception:
            typer.echo(f"Not a valid nem file: {fp}")
    typer.echo(f"Finished exporting to DB.")
