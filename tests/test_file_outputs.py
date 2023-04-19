from pathlib import Path

from nemreader import (
    nmis_in_file,
    output_as_csv,
    output_as_daily_csv,
    output_as_data_frames,
)


def test_nmi_output():
    """Check NMIs in file"""
    file_name = "examples/unzipped/Example_NEM12_multiple_meters.csv"
    items = list(nmis_in_file(file_name))
    nmis = [x[0] for x in items]
    assert "NCDE001111" in nmis
    assert "NDDD001888" in nmis

    suffixes = [x[1] for x in items]
    assert "E1" in suffixes[0]
    assert "E1" not in suffixes[1]
    assert "B1" in suffixes[1]


def test_csv_output(tmp_path: Path):
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_files = output_as_csv(file_name, output_dir=tmp_path)
    assert len(output_files) == 1


def test_daily_csv_output(tmp_path: Path):
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_file = output_as_daily_csv(file_name, output_dir=tmp_path)
    assert "Example_NEM12_actual_interval_daily_totals.csv" in str(output_file)


def test_data_frame_output():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_dfs = output_as_data_frames(file_name)
    for nmi, df in output_dfs:
        assert type(nmi) == str
        assert df["quality_method"][0] == "A"


def test_data_frame_output_different_interval():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM12_different_interval_length.csv"
    output_dfs = output_as_data_frames(file_name)
    nmi, df = output_dfs[0]  # Return data for first NMI in file
    assert type(nmi) == str
    assert df["V1"].count() == 144
    assert df["E1"].count() == 48


def test_data_frame_output_nem13():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM13_forward_estimate.csv"
    output_dfs = output_as_data_frames(file_name)
    for nmi, df in output_dfs:
        print(df.head())
        assert type(nmi) == str
        assert df["quality_method"][0] == "E64"
