import numpy as np
import pandas as pd

from nemreader import NEMFile


def test_unit_capitalisation():
    """Check that capitalisation of units does not affect the sum/aggregation
    of data when resampling the data."""

    nf = NEMFile("examples/unzipped/Example_NEM12_upper_case_units.csv", strict=True)
    meter_data = nf.nem_data()

    df_15min = nf.get_pivot_data_frame(split_days=True, set_interval=15)
    df_30min = nf.get_pivot_data_frame(split_days=True, set_interval=30)
    df_60min = nf.get_pivot_data_frame(split_days=True, set_interval=60)

    for nmi, nmi_readings in meter_data.readings.items():
        for key in nmi_readings.keys():
            assert nmi_readings[key][0].t_end - nmi_readings[key][
                0
            ].t_start == pd.Timedelta(minutes=30)
            assert "H" in nmi_readings[key][0].uom

        nmi_df_15min = df_15min[(df_15min["nmi"] == nmi)]
        nmi_df_30min = df_30min[(df_30min["nmi"] == nmi)]
        nmi_df_60min = df_60min[(df_60min["nmi"] == nmi)]
        # Units are in KWH - expect the values to be summed
        np.testing.assert_allclose(
            np.sum(nmi_df_30min["E1"]), np.sum(nmi_df_60min["E1"])
        )
        np.testing.assert_allclose(
            np.sum(nmi_df_30min["E1"]), np.sum(nmi_df_15min["E1"])
        )
