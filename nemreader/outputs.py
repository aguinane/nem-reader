"""
    nemreader.outputs
    ~~~~~
    Output results in different formats
"""

import csv
from nemreader import read_nem_file



def output_as_csv(file_name, nmi=None, output_file=None):
    """
    Transpose all channels and output a csv that is easier
    to read and do charting on

    :param file_name: The NEM file to process
    :param nmi: Which NMI to output if more than one
    :param output_file: Specify different output location
    :returns: The file that was created
    """
    
    m = read_nem_file(file_name)
    if nmi is None:
        nmi = list(m.readings.keys())[0]  # Use first NMI

    channels = list(m.transactions[nmi].keys())
    num_records = len(m.readings[nmi][channels[0]])
    last_date = m.readings[nmi][channels[0]][-1].t_end
    if output_file is None:
        output_file = '{}_{}_transposed.csv'.format(nmi, last_date.strftime('%Y%m%d'))
    with open(output_file, 'w', newline='') as csvfile:
        cwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        heading_list = ['period_start','period_end']
        for channel in channels:
            heading_list.append(channel)
        heading_list.append('quality_method')
        cwriter.writerow(heading_list)

        for i in range(0, num_records):
            t_start = m.readings[nmi][channels[0]][i].t_start
            t_end = m.readings[nmi][channels[0]][i].t_end
            quality_method = m.readings[nmi][channels[0]][i].quality_method
            row_list = [t_start, t_end]
            for ch in channels:
                val = m.readings[nmi][ch][i].read_value
                row_list.append(val)
            row_list.append(quality_method)
            cwriter.writerow(row_list)
    return output_file
