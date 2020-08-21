from easydev import TempFile
import subprocess
from fitter.main import fitdist

# generate dummy data 
from scipy import stats
data1 = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)
data2 = stats.gamma.rvs(1, loc=1.5, scale=3, size=10000)
tt = open("test.csv", "w")
for x, y in zip(data1, data2):
    tt.write("{},{}\n".format(x,y))



def test_main_app():
    from click.testing import CliRunner
    runner = CliRunner()

    results = runner.invoke(fitdist, ['--help'])
    assert results.exit_code == 0
    with TempFile() as fin:
        tt = open(fin.name, "w")
        for x, y in zip(data1, data2):
            tt.write("{},{}\n".format(x,y))
        results = runner.invoke(fitdist, [fin.name, "--no-verbose"])
        assert results.exit_code == 0
        results = runner.invoke(fitdist, [fin.name, "--progress", "--column-number", 1])
        assert results.exit_code == 0
        # here, fitter.log and fitter.png have been created. FIXME should remove
        # them properly


