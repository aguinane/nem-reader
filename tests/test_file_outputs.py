from nemreader import output_as_csv
from nemreader import output_as_daily_csv
from nemreader import output_as_data_frames


def test_csv_output(tmpdir):
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_files = output_as_csv(file_name, output_dir=tmpdir)
    assert len(output_files) == 1


def test_daily_csv_output(tmpdir):
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_file = output_as_daily_csv(file_name, output_dir=tmpdir)
    assert "Example_NEM12_actual_interval_daily_totals.csv" in str(output_file)


def test_data_frame_output():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    output_dfs = output_as_data_frames(file_name)
    for nmi, df in output_dfs:
        assert type(nmi) == str
        assert df["quality_method"][0] == "A"


def test_data_frame_output_nem13():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM13_forward_estimate.csv"
    output_dfs = output_as_data_frames(file_name)
    for nmi, df in output_dfs:
        print(df.head())
        assert type(nmi) == str
        assert df["quality_method"][0] == "E64"
