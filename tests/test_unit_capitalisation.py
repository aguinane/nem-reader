from datetime import timedelta

import polars as pl

from nemreader import NEMFile


def test_unit_capitalisation():
    """Check that capitalisation of units does not affect the sum/aggregation
    of data when resampling the data."""

    nf = NEMFile("examples/unzipped/Example_NEM12_upper_case_units.csv", strict=True)
    meter_data = nf.nem_data()

    df_15min = nf.get_data_frame_wide(split_days=True, set_interval=15)
    df_30min = nf.get_data_frame_wide(split_days=True, set_interval=30)
    df_60min = nf.get_data_frame_wide(split_days=True, set_interval=60)

    for nmi, nmi_readings in meter_data.readings.items():
        for key in nmi_readings:
            assert nmi_readings[key][0].t_end - nmi_readings[key][
                0
            ].t_start == timedelta(minutes=30)
            assert "H" in nmi_readings[key][0].uom

        nmi_df_15min = df_15min.filter(pl.col("nmi") == nmi)
        nmi_df_30min = df_30min.filter(pl.col("nmi") == nmi)
        nmi_df_60min = df_60min.filter(pl.col("nmi") == nmi)
        # Units are in KWH - expect the values to be summed
        assert abs(
            nmi_df_30min["E1"].sum() - nmi_df_60min["E1"].sum()
        ) < 1e-9
        assert abs(
            nmi_df_30min["E1"].sum() - nmi_df_15min["E1"].sum()
        ) < 1e-9
