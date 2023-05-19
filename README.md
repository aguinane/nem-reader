# nem-reader

![Python package](https://github.com/aguinane/nem-reader/workflows/Python%20package/badge.svg?branch=master)
[![PyPI version](https://img.shields.io/pypi/pyversions/nemreader?color=%2344CC11)](https://pypi.org/project/nemreader/)
[![PyPi downloads](https://img.shields.io/pypi/dw/nemreader?label=downloads@pypi&color=344CC11)](https://pypi.org/project/nemreader/)
[![Documentation Status](https://readthedocs.org/projects/nem-reader/badge/?version=latest)](https://nem-reader.readthedocs.io/en/latest/?badge=latest)

The Australian Energy Market Operator (AEMO) defines a [Meter Data File Format (MDFF)](https://www.aemo.com.au/Stakeholder-Consultation/Consultations/Meter-Data-File-Format-Specification-NEM12-and-NEM13) for reading energy billing data.
This library sets out to parse these NEM12 (interval metering data) and NEM13 (accumulated metering data) data files into a useful python object, for use in other projects.

---

**[Read the documentation on ReadTheDocs!](https://nem-reader.readthedocs.io/en/latest/)**

---
## Install

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

```sh
pip install nemreader
```

