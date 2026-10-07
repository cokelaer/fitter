from pathlib import Path

import pytest
from scipy import stats

from fitter.main import fitdist, show_distributions


@pytest.fixture
def setup_teardown():
    # generate dummy data
    data1 = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)
    data2 = stats.gamma.rvs(1, loc=1.5, scale=3, size=10000)
    with open("test.csv", "w") as tmp:
        tmp.writelines(f"{x},{y}\n" for x, y in zip(data1, data2))

    # hand over control to test
    yield

    # remove files left by testing
    filenames = ["test.csv", "fitter.log", "fitter.png"]
    for filename in filenames:
        file = Path(filename)
        if file.exists():
            file.unlink()


def test_main_app(setup_teardown):
    from click.testing import CliRunner

    runner = CliRunner()

    results = runner.invoke(fitdist, ["--help"])
    assert results.exit_code == 0

    results = runner.invoke(fitdist, ["test.csv", "--no-verbose"])
    assert results.exit_code == 0

    results = runner.invoke(fitdist, ["test.csv", "--progress", "--column-number", 1])
    assert results.exit_code == 0

    results = runner.invoke(show_distributions, [])
    assert results.exit_code == 0

    results = runner.invoke(fitdist, ["test.csv", "--output-image", "test.dummy"])
    assert results.exit_code == 1


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _invoke(*args):
    from click.testing import CliRunner

    return CliRunner().invoke(fitdist, list(args))


def test_missing_file(workdir):
    result = _invoke("missing.csv")
    assert result.exit_code == 1
    assert "not found" in result.output


def test_missing_column(workdir):
    (workdir / "data.csv").write_text("1.0,2.0\n3.0,4.0\n")
    result = _invoke("data.csv", "--column-number", 5)
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_non_float_value(workdir):
    (workdir / "data.csv").write_text("abc,2.0\n")
    result = _invoke("data.csv")
    assert result.exit_code == 1
    assert "Cannot convert" in result.output


def test_empty_distributions(workdir):
    (workdir / "data.csv").write_text("1.0\n2.0\n3.0\n")
    result = _invoke("data.csv", "--distributions", " , ")
    assert result.exit_code == 1
    assert "No distributions" in result.output


def test_unknown_distribution(workdir):
    (workdir / "data.csv").write_text("1.0\n2.0\n3.0\n")
    result = _invoke("data.csv", "--distributions", "gamma,normal")
    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)


def test_unreadable_input(workdir):
    (workdir / "data.csv").write_bytes(b"\xff\xfe\x00")
    result = _invoke("data.csv")
    assert result.exit_code != 0


def test_log_file_write_failure(workdir):
    (workdir / "data.csv").write_text("\n".join(str(x) for x in stats.gamma.rvs(2, size=200)))
    (workdir / "bad.log").mkdir()  # a directory: write_text raises OSError
    result = _invoke("data.csv", "--distributions", "gamma", "--tag", "bad", "--no-verbose")
    assert result.exit_code == 0
    assert "Could not write log file" in result.output


def test_os_error_while_reading(workdir, monkeypatch):
    (workdir / "data.csv").write_text("1.0\n2.0\n")

    def boom(self, *args, **kwargs):
        raise OSError("disk on fire")

    monkeypatch.setattr(Path, "open", boom)
    result = _invoke("data.csv")
    assert result.exit_code == 1
    assert "Error reading file" in result.output
