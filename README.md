# nem-reader

[![Build Status](https://travis-ci.org/aguinane/nem-reader.svg?branch=master)](https://travis-ci.org/aguinane/nem-reader) [![Coverage Status](https://coveralls.io/repos/github/aguinane/nem-reader/badge.svg)](https://coveralls.io/github/aguinane/nem-reader)

The Australian Energy Market Operator (AEMO) defines a Meter Data File Format (MDFF) for reading energy billing data.
[MDFF Specification](https://www.aemo.com.au/Stakeholder-Consultation/Consultations/Meter-Data-File-Format-Specification-NEM12-and-NEM13)

This library sets out to parse these NEM12 (interval metering data) and NEM13 (accumulated metering data) data files into a useful python object, for use in other projects.

First, read in the NEM file:
```
import nemreader as nr
m = nr.read_nem_file(file_path)
```

Then retreive the data for the NMI and channels of interest:
```
> print(m.header)
HeaderRecord(version_header='NEM12', datetime=datetime.datetime(2004, 4, 20, 13, 0), from_participant='MDA1', to_participant='Ret1')

> print('Transactions:', m.transactions)
Transactions: {'CCCC123456': {'E1': []}}

> for nmi in m.readings:
>     for channel in m.readings[nmi]:
>         for reading in m.readings[nmi][channel][-1:]:
>             print(reading)
Reading(t_start=datetime.datetime(2004, 4, 17, 23, 30), t_end=datetime.datetime(2004, 4, 18, 0, 0), read_value=14.733, uom='kWh', quality_method='S14', event='', read_start=None, read_end=None)
```