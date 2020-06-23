# nem-reader

[![PyPI version](https://badge.fury.io/py/nemreader.svg)](https://badge.fury.io/py/nemreader) ![Python package](https://github.com/aguinane/nem-reader/workflows/Python%20package/badge.svg?branch=develop) [![Coverage Status](https://coveralls.io/repos/github/aguinane/nem-reader/badge.svg)](https://coveralls.io/github/aguinane/nem-reader)

The Australian Energy Market Operator (AEMO) defines a [Meter Data File Format (MDFF)](https://www.aemo.com.au/Stakeholder-Consultation/Consultations/Meter-Data-File-Format-Specification-NEM12-and-NEM13) for reading energy billing data.
This library sets out to parse these NEM12 (interval metering data) and NEM13 (accumulated metering data) data files into a useful python object, for use in other projects.

## Usage

First, read in the NEM file:
```python
from nemreader import read_nem_file
m = read_nem_file('examples/unzipped/Example_NEM12_actual_interval.csv')
```

You can see what data for the NMI and suffix (channel) is available:
```python
> print(m.header)
HeaderRecord(version_header='NEM12', creation_date=datetime.datetime(2004, 4, 20, 13, 0), from_participant='MDA1', to_participant='Ret1')

> print(m.transactions)
{'VABD000163': {'E1': [], 'Q1': []}}
```

Standard suffix/channels are defined in the [National Metering Identifier Procedure](https://www.aemo.com.au/-/media/Files/Electricity/NEM/Retail_and_Metering/Metering-Procedures/2018/MSATS-National-Metering-Identifier-Procedure.pdf).
`E1` is the general consumption channel (`11` for NEM13).

Most importantly, you will want to get the energy data itself:

```python
> for nmi in m.readings:
>     for channel in m.readings[nmi]:
>         for reading in m.readings[nmi][suffix][-1:]:
>             print(reading)
Reading(t_start=datetime.datetime(2004, 4, 17, 23, 30), t_end=datetime.datetime(2004, 4, 18, 0, 0), read_value=14.733, uom='kWh', quality_method='S14', event='', read_start=None, read_end=None)
```

## Command Line Usage

You can also output the NEM file in a more human readable format:

```shell
nemreader output example.zip
```

Which outputs transposed values to a csv file for all channels:

```
period_start,period_end,E1,Q1,quality_method
2004-02-01 00:00:00,2004-02-01 00:30:00,1.111,2.222,A
2004-02-01 00:30:00,2004-02-01 01:00:00,1.111,2.222,A
...
```

## Charting

You can easily chart the usage data using pandas:

```python
import matplotlib.pyplot as plt
from nemreader import output_as_data_frames

# Setup Pandas DataFrame
dfs = output_as_data_frames("examples/nem12/NEM12#000000000000002#CNRGYMDP#NEMMCO.zip")
nmi, df = dfs[0] # Return data for first NMI in file
df.set_index("period_start", inplace=True)

# Chart time of day profile
hourly = df.groupby([(df.index.hour)]).sum()
plot = hourly.plot(title=nmi, kind="bar", y=["E1"])
plt.show()
```

!["Time of day plot"](docs/plot_profile.png)

Or even generate a calendar with daily usage totals:

```python
# Chart daily usage calendar
import pandas as pd
import calmap
plot = calmap.calendarplot(pd.Series(df.E1), daylabels="MTWTFSS")
plt.show()
```

!["Calendar Plot"](docs/plot_cal.png)
