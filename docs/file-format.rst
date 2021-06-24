File Format
======================================

The Australian Energy Market Operator (AEMO) defines a 
`Meter Data File Format (MDFF) <https://www.aemo.com.au/Stakeholder-Consultation/Consultations/Meter-Data-File-Format-Specification-NEM12-and-NEM13>`_ 
for reading energy billing data.
This library sets out to parse these NEM12 (interval metering data) and NEM13 (accumulated metering data) data files into a useful python object, for use in other projects.


AEMO also publish a bunch of example files such as these 
`NEM12 examples <https://www.aemo.com.au/-/media/files/electricity/nem/retail_and_metering/metering-procedures/2016/nem12-example-files.zip>`_.

Standard suffix/channels are defined in the 
`National Metering Identifier Procedure <https://www.aemo.com.au/-/media/Files/Electricity/NEM/Retail_and_Metering/Metering-Procedures/2018/MSATS-National-Metering-Identifier-Procedure.pdf>`_.

Of particular note is that the terms export/import are from the grid and not relative to the customer.

   All flows are specified by reference to their direction to or from the market. Hence:
      (i) All energy from the market is considered export (i.e. energy consumed by an End User is export) (Export).
      (ii) All energy into the market is considered import (i.e. the energy generated into the market is import) (Import).

So for most residential customers:

* `E1` is the general consumption channel (`11` for NEM13).
* `E2` is the controlled load channel
* `B1` is the export (Solar PV) channel 

.. image:: _static/img/nmi-suffixes.jpg

.. image:: _static/img/nmi-suffixes2.png

