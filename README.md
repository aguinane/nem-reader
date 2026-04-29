# nem-reader

[![PyPI version](https://img.shields.io/pypi/pyversions/nemreader)][pypi]
[![PyPi downloads](https://img.shields.io/pypi/dw/nemreader)][pypi]

[pypi]: https://pypi.org/project/nemreader/


The Australian Energy Market Operator (AEMO) defines a [Meter Data File Format (MDFF)][mdff] for reading energy billing data. When you request energy data from your distribution utility or retailer, this is probably the format it will come in. 

- NEM12 for interval data (smart meters)
- NEM13 for accumilation data (old style meters)

[mdff]: https://www.aemo.com.au/Stakeholder-Consultation/Consultations/Meter-Data-File-Format-Specification-NEM12-and-NEM13

Whilst it is a pretty clever file format for sharing this data efficiently - it's not very helpful if you want to just chart it in excel.
This library sets out to parse these data files into either a CSV (Excel) file or Python dataframe.

## The File Format and Meter Channels

To understand the actual file format, you'll want to read the MDFF spec and the [National Metering Identifier Procedure (NMIP)][nmip]. AEMO also publish a bunch of example files such as these [NEM12
examples][nem12-ex].

[nmip]: (https://www.aemo.com.au/-/media/Files/Electricity/NEM/Retail_and_Metering/Metering-Procedures/2018/MSATS-National-Metering-Identifier-Procedure.pdf)
[nem12-ex]: https://www.aemo.com.au/-/media/files/electricity/nem/retail_and_metering/metering-procedures/2016/nem12-example-files.zip


The most important thing to know is that the terms export/import are referenced from the grid and not relative to the customer. So when it talks about export channels it means importing power from the grid and not solar exports. 

So for most residential customers:
-   `E1` is the general consumption channel
    (`11` for NEM13).
-   `E2` is the controlled load channel
-   `B1` is the export (Solar PV) channel


## Export to CSV

You can quickly output the NEM file in a more human readable format using the command line:

``` bash
nemreader output-csv "examples/nem12/nem12#S01#INTEGM#NEMMCO.zip"
```

Which outputs transposed values to a csv file for all channels:

| t_start             | t_end               | quality | evt_code | evt_desc | Q1    | E1    |
| ------------------- | ------------------- | ------- | -------- | -------- | ----- | ----- |
| 2004-02-01 00:00:00 | 2004-02-01 00:30:00 | A       |          |          | 2.222 | 1.111 |
| 2004-02-01 00:30:00 | 2004-02-01 01:00:00 | A       |          |          | 2.222 | 1.111 |


## Export to DataFrame

You can return the data as a polars dataframe.

``` python
from nemreader import NEMFile
m = NEMFile('examples/unzipped/Example_NEM12_actual_interval.csv')
df = m.get_data_frame_long()
print(df)
```

```df
           nmi suffix      serno             t_start               t_end  value quality evt_code evt_desc
0   VABD000163     E1  METSER123 2004-02-01 00:00:00 2004-02-01 00:30:00  1.111       A                  
1   VABD000163     E1  METSER123 2004-02-01 00:30:00 2004-02-01 01:00:00  1.111       A                  
2   VABD000163     E1  METSER123 2004-02-01 01:00:00 2004-02-01 01:30:00  1.111       A                  
3   VABD000163     E1  METSER123 2004-02-01 01:30:00 2004-02-01 02:00:00  1.111       A                  
4   VABD000163     E1  METSER123 2004-02-01 02:00:00 2004-02-01 02:30:00  1.111       A                  
..         ...    ...        ...                 ...                 ...    ...     ...      ...      ...
43  VABD000163     Q1  METSER123 2004-02-01 21:30:00 2004-02-01 22:00:00  2.222       A                  
44  VABD000163     Q1  METSER123 2004-02-01 22:00:00 2004-02-01 22:30:00  2.222       A                  
45  VABD000163     Q1  METSER123 2004-02-01 22:30:00 2004-02-01 23:00:00  2.222       A                  
46  VABD000163     Q1  METSER123 2004-02-01 23:00:00 2004-02-01 23:30:00  2.222       A                  
47  VABD000163     Q1  METSER123 2004-02-01 23:30:00 2004-02-02 00:00:00  2.222       A      
```

Depending on the use case, the *wide* form of the dataframe might be preferred over the *long* form. This is the form used when exporting to CSV using the command line. It will group up the various channels and match them by timestamp. 

``` python
df = m.get_data_frame_wide()
print(df)
```

```df
               nmi             t_start               t_end quality evt_code evt_desc     E1     Q1
0       VABD000163 2004-02-01 00:00:00 2004-02-01 00:30:00       A                    1.111  2.222
1       VABD000163 2004-02-01 00:30:00 2004-02-01 01:00:00       A                    1.111  2.222
2       VABD000163 2004-02-01 01:00:00 2004-02-01 01:30:00       A                    1.111  2.222
3       VABD000163 2004-02-01 01:30:00 2004-02-01 02:00:00       A                    1.111  2.222
4       VABD000163 2004-02-01 02:00:00 2004-02-01 02:30:00       A                    1.111  2.222
5       VABD000163 2004-02-01 02:30:00 2004-02-01 03:00:00       A                    1.111  2.222
6       VABD000163 2004-02-01 03:00:00 2004-02-01 03:30:00       A                    1.111  2.222
7       VABD000163 2004-02-01 03:30:00 2004-02-01 04:00:00       A                    1.111  2.222
8       VABD000163 2004-02-01 04:00:00 2004-02-01 04:30:00       A                    1.111  2.222
```
