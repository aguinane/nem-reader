import pytest

from nemreader import NEMFile


# TODO: See if this test can be made to work again
@pytest.mark.skip(reason="breaks other use cases")
def test_30min_200_15min_300():
    with pytest.raises(ValueError):
        nf = NEMFile(
            "examples/invalid/Example_NEM12_30min_200_15min_300.csv", strict=False
        )
        nf.nem_data()


def test_15min_200_30min_300():
    with pytest.raises(ValueError):
        nf = NEMFile(
            "examples/invalid/Example_NEM12_15min_200_30min_300.csv", strict=False
        )
        nf.nem_data()


def test_30min_200_15min_400():
    with pytest.raises(ValueError):
        nf = NEMFile(
            "examples/invalid/Example_NEM12_30min_200_15min_400.csv", strict=False
        )
        nf.nem_data()


@pytest.mark.skip(reason="need to rearchitect parser to detect this")
def test_15min_200_30min_400():
    with pytest.raises(ValueError):
        nf = NEMFile(
            "examples/invalid/Example_NEM12_15min_200_30min_400.csv", strict=False
        )
        nf.nem_data()
