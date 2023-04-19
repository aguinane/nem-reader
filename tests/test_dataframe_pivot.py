from nemreader import NEMFile


def test_pivot_dataframe():
    nf = NEMFile("examples/Example_different_intervals.zip", strict=True)

    # The intervals are different, so we have 48 30min + 144 10min = 192 rows
    df = nf.get_pivot_data_frame()
    for suffix in ["t_start", "E1", "E2", "V1", "quality", "evt_code", "evt_desc"]:
        assert suffix in df.columns
    assert len(df) == 192

    # Check splitting to 10 min
    df = nf.get_pivot_data_frame(set_interval=10)
    for suffix in ["t_start", "E1", "E2", "V1", "quality", "evt_code", "evt_desc"]:
        assert suffix in df.columns
    assert len(df) == 144

    # Check grouping to 30 min
    df = nf.get_pivot_data_frame(set_interval=30)
    for suffix in ["t_start", "E1", "E2", "V1", "quality", "evt_code", "evt_desc"]:
        assert suffix in df.columns
    assert len(df) == 48
