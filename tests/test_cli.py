import pytest
from typer.testing import CliRunner

from nemreader.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_version(runner):
    result = runner.invoke(app, ["--version"])
    assert "nemreader version:" in result.stdout
    assert result.exit_code == 0


def test_cli_list_nmis(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(app, ["list-nmis", file_name, "--verbose"])
    assert "The following NMI[suffix] exist in this file:" in result.stdout
    assert result.exit_code == 0


def test_cli_csv(runner):
    file_name = "examples/invalid/Example_NEM12_missing_header.csv"
    result = runner.invoke(app, ["output-csv", file_name, "--verbose"])
    assert "Created" in result.stdout
    assert result.exit_code == 0


def test_cli_csv_daily(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(app, ["output-csv-daily", file_name, "--verbose"])
    assert "Created" in result.stdout
    assert result.exit_code == 0


def test_cli_sqlite(runner):
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    result = runner.invoke(app, ["output-sqlite", file_name, "--verbose"])
    assert "Finished exporting to DB." in result.stdout
    assert result.exit_code == 0


def test_cli_sqlite_dir(runner):
    file_dir = "examples/unzipped/"
    result = runner.invoke(app, ["output-sqlite", file_dir, "--verbose"])
    assert "Finished exporting to DB." in result.stdout
    assert result.exit_code == 0
