import logging
import click
from nemreader import nmis_in_file
from nemreader import output_as_csv
from nemreader import output_as_daily_csv
from nemreader import __version__

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"


@click.group()
@click.version_option(version=__version__, prog_name="nemreader")
def cli():
    """nemreader

    Parse AEMO NEM12 and NEM13 meter data files
    """
    pass


@cli.command("list-nmis")
@click.argument("nemfile", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Will print verbose messages.")
def list_nmis(nemfile, verbose):
    """ Output list of NMIs in NEM file """

    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    nmis = list(nmis_in_file(nemfile))
    click.echo("The following NMI[suffix] exist in this file:")
    for nmi, suffixes in nmis:
        suffix_str = ",".join(suffixes)
        click.echo(f"{nmi}[{suffix_str}]")


@cli.command("output")
@click.argument("nemfile", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Will print verbose messages.")
@click.option(
    "--outdir",
    "-o",
    type=click.Path(exists=True),
    default=".",
    help="The output folder to save to",
)
def output(nemfile, verbose, outdir):
    """ Output NEM file to transposed CSV.

    NEMFILE is the name of the file to parse.
    """
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    for fname in output_as_csv(nemfile, output_dir=outdir):
        click.echo(f"Created {fname}")


@cli.command("output-daily")
@click.argument("nemfile", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Will print verbose messages.")
@click.option(
    "--outdir",
    "-o",
    type=click.Path(exists=True),
    default=".",
    help="The output folder to save to",
)
def output_daily(nemfile, verbose, outdir):
    """ Output NEM file to transposed CSV.

    NEMFILE is the name of the file to parse.
    """
    if verbose:
        log_level = "DEBUG"
    else:
        log_level = "WARNING"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    fname = output_as_daily_csv(nemfile, output_dir=outdir)
    click.echo(f"Created {fname}")
