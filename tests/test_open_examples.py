import os

from nemreader import NEMFile


def test_unzipped_examples():
    """Open and parse unzipped example files"""

    skips = ["Example_NEM12_powercor.csv", "Example_NEM12_powercor_missing_fields.csv"]
    test_path = os.path.abspath("examples/unzipped")
    for file_name in os.listdir(test_path):
        if file_name in skips:
            continue
        test_file = os.path.join(test_path, file_name)
        nf = NEMFile(test_file, strict=True)
        meter_data = nf.nem_data()
        assert meter_data.header.version_header in ["NEM12", "NEM13"]


def test_nem12_examples():
    """Open and parse zipped NEM12 example files"""
    skips = [
        "NEM12#Scenario10#ETSAMDP#NEMMCO.zip",  # 300 Row has new line
        "Example_NEM12_powercor.csv.zip",
    ]
    test_path = os.path.abspath("examples/nem12")
    for file_name in os.listdir(test_path):
        if file_name in skips:
            continue
        test_file = os.path.join(test_path, file_name)
        nf = NEMFile(test_file, strict=True)
        meter_data = nf.nem_data()
        assert meter_data.header.version_header == "NEM12"


def test_nem13_examples():
    """Open and parse zipped NEM13 example files"""

    test_path = os.path.abspath("examples/nem13")
    for file_name in os.listdir(test_path):
        test_file = os.path.join(test_path, file_name)
        nf = NEMFile(test_file, strict=True)
        meter_data = nf.nem_data()
        assert meter_data.header.version_header == "NEM13"
