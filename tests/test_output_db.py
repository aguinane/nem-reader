from sqlite_utils import Database

from nemreader import output_as_sqlite


def test_db_output():
    """Create a pandas dataframe"""
    file_name = "examples/unzipped/Example_NEM12_actual_interval.csv"
    fp = output_as_sqlite(file_name, set_interval=5, replace=True)
    assert fp.name == "nemdata.db"

    db = Database(fp)
    rows = list(db.query("select * from nmi_summary"))
    assert len(rows) == 2
    assert rows[0]["nmi"] == "VABD000163"
