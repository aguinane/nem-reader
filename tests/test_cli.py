import pytest
from click.testing import CliRunner
from nemreader.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli(runner):
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert not result.exception
    assert "nemreader" in result.output.strip()


def test_cli_list_nmis(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(cli, ["list-nmis", file_name, "--verbose"])
    assert "The following NMI[suffix] exist in this file:" in result.output.strip()
    assert result.exit_code == 0
