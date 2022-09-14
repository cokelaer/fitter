import pytest
from pathlib import Path
import subprocess
from scipy import stats
from fitter.main import fitdist
from fitter.main import show_distributions

@pytest.fixture
def setup_teardown():
    # generate dummy data
    data1 = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)
    data2 = stats.gamma.rvs(1, loc=1.5, scale=3, size=10000)
    with open("test.csv", "w") as tmp:
        for x, y in zip(data1, data2):
            tmp.write("{},{}\n".format(x,y))

    # hand over control to test
    yield

    # remove files left by testing
    filenames = ['test.csv', 'fitter.log', 'fitter.png']
    for filename in filenames:
        file = Path(filename)
        if file.exists():
            file.unlink()


def test_main_app(setup_teardown):
    from click.testing import CliRunner
    runner = CliRunner()

    results = runner.invoke(fitdist, ['--help'])
    assert results.exit_code == 0

    results = runner.invoke(fitdist, ['test.csv', "--no-verbose"])
    assert results.exit_code == 0

    results = runner.invoke(fitdist, ['test.csv', "--progress", "--column-number", 1])
    assert results.exit_code == 0

    results = runner.invoke(show_distributions, [])
    assert results.exit_code == 0
