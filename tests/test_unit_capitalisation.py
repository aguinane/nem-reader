import nemreader as nr
import pytest
import pandas as pd
import numpy as np


def test_unit_capitalisation():
    """Check that capitalisation of units does not affect the sum/aggregation
    of data when resampling the data."""
    meter_data = nr.read_nem_file("examples/unzipped/Example_NEM12_upper_case_units.csv")

    for (nmi, nmi_readings) in meter_data.readings.items():
        for key in nmi_readings.keys():
            assert nmi_readings[key][0].t_end - nmi_readings[key][0].t_start == pd.Timedelta(minutes=30)
            assert "H" in nmi_readings[key][0].uom

        channels = list(meter_data.transactions[nmi])
        nmi_df_15min = nr.outputs.get_data_frame(
            channels,
            nmi_readings,
            split_days=True,
            set_interval=15,
        )
        nmi_df_30min = nr.outputs.get_data_frame(
            channels,
            nmi_readings,
            split_days=True,
            set_interval=30,
        )
        nmi_df_60min = nr.outputs.get_data_frame(
            channels,
            nmi_readings,
            split_days=True,
            set_interval=60,
        )
        # Units are in KWH - expect the values to be summed
        np.testing.assert_allclose(np.sum(nmi_df_30min["E1"]), np.sum(nmi_df_60min["E1"]))
        np.testing.assert_allclose(np.sum(nmi_df_30min["E1"]), np.sum(nmi_df_15min["E1"]))
