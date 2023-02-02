from nemreader import NEMFile


def test_many_nmis():
    """Test a file with lots of NMIs in it"""
    file_name = "examples/Example_NEM12_ManyNMIs.zip"
    nf = NEMFile(file_name, strict=True)
    df = nf.get_data_frame()
    assert len(df) == 57024
