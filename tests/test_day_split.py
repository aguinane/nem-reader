import pandas as pd

from nemreader.outputs import output_as_data_frames


def test_split_interval():
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"

    for _, df in output_as_data_frames(file_name, set_interval=1):
        first = df.iloc[0]
        delta = pd.Timedelta(first.t_end - first.t_start).seconds
        assert delta == 60 * 1

        assert first.E1 == 1.111 / 30


def test_group_interval():
    """Create a temporary csv output"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"

    for _, df in output_as_data_frames(file_name, set_interval=60):
        first = df.iloc[0]
        delta = pd.Timedelta(first.t_end - first.t_start).seconds
        assert delta == 60 * 60

        assert first.E1 == 1.111 * 2
