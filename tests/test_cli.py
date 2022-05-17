import pytest
from nemreader.cli import app
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_list_nmis(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(app, ["list-nmis", file_name, "--verbose"])
    assert "The following NMI[suffix] exist in this file:" in result.stdout
    assert result.exit_code == 0


def test_cli_sqlite(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(app, ["output-sqlite", file_name, "--verbose"])
    assert "Finished exporting to DB." in result.stdout
    assert result.exit_code == 0
