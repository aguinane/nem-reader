import logging
import click
from nemreader import nmis_in_file
from nemreader import output_as_csv

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"


@click.group()
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
        logging.basicConfig(level="DEBUG", format=LOG_FORMAT)
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
        logging.basicConfig(level="DEBUG", format=LOG_FORMAT)
    for fname in output_as_csv(nemfile, output_dir=outdir):
        click.echo(f"Created {fname}")
