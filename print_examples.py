import nemreader as nr

def print_meter_record(file_path, rows=5):
    """ Output readings for specified number of rows to console """
    m = nr.read_nem_file(file_path)
    print(m.header)
    for nmi in m.readings:
        for channel in m.readings[nmi]:
            print(nmi, 'Channel', channel)
            for reading in m.readings[nmi][channel][-rows:]:
                print('', reading)


if __name__ == '__main__':
    print('Example NEM12 - Actual Interval:')
    print('-' * 10)
    print_meter_record('examples/Example_NEM12_actual_interval.csv', 5)

    print('\nExample NEM12 - Substituted Interval:')
    print('-' * 10)
    print_meter_record('examples/Example_NEM12_substituted_interval.csv', 5)

    print('\nExample NEM12 - Multiple Quality Methods:')
    print('-' * 10)
    print_meter_record('examples/Example_NEM12_multiple_quality.csv', 5)

    print('\nExample NEM13 - Actual Read:')
    print('-' * 10)
    print_meter_record('examples/Example_NEM13_consumption_data.csv', 5)

    print('\nExample NEM13 - Forward Estimates:')
    print('-' * 10)
    print_meter_record('examples/Example_NEM13_forward_estimate.csv', 5)

    print('\nReal NEM13 Example:')
    print('-' * 10)
    print_meter_record('examples/NEM13#DATA_14121801#WBAYM#3044076134.V01', 5)

    print('\nReal NEM12 Example:')
    print('-' * 10)
    print_meter_record('examples/NEM12#DATA_16081001#WBAYM#3044076134.V01', 5)
