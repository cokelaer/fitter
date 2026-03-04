from fitter import Fitter, get_common_distributions, get_distributions


def test_dist():
    assert "gamma" in get_common_distributions()
    assert len(get_distributions()) > 40


def test_fitter():
    f = Fitter([1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3], distributions=["gamma"], xmin=0, xmax=4)
    try:
        f.plot_pdf()
    except Exception:
        pass
    f.fit()
    f.summary()
    assert f.xmin == 0
    assert f.xmax == 4

    # reset the range:
    f.xmin = None
    f.xmax = None
    assert f.xmin == 1
    assert f.xmax == 3

    f = Fitter([1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3], distributions=["gamma"])
    f.fit(progress=True)
    f.summary()
    assert f.xmin == 1
    assert f.xmax == 3


def test_gamma():
    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)

    f = Fitter(data, bins=100)
    f.xmin = -10  # should have no effect
    f.xmax = 1000000  # no effect
    f.xmin = 0.1
    f.xmax = 10
    f.distributions = ["gamma", "alpha"]
    f.fit()
    df = f.summary()
    assert len(df)

    f.plot_pdf(names=["gamma"])
    f.plot_pdf(names="gamma")

    res = f.get_best()
    assert "gamma" in res.keys()


def test_others():
    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)
    f = Fitter(data, bins=100, distributions="common")
    f.fit()
    assert f.df_errors.loc["gamma"].loc["aic"] > 100

    f = Fitter(data, bins=100, distributions="gamma")
    f.fit()
    assert f.df_errors.loc["gamma"].loc["aic"] > 100


def test_n_jobs_api():
    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)
    f = Fitter(data, distributions="common")
    f.fit(n_jobs=-1)
    f.fit(n_jobs=1)


def test_verbose():
    """Test that verbose=False suppresses log output without affecting fit results."""
    from loguru import logger
    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)

    # Capture log messages when verbose=True.
    # Use prefer="threads" so logging happens in the same process and can be captured.
    verbose_messages = []
    handler_id = logger.add(lambda msg: verbose_messages.append(msg), level="INFO")
    try:
        f_verbose = Fitter(data, distributions=["gamma", "norm"], verbose=True)
        f_verbose.fit(prefer="threads")
    finally:
        logger.remove(handler_id)

    # Capture log messages when verbose=False (should be empty)
    silent_messages = []
    handler_id = logger.add(lambda msg: silent_messages.append(msg), level="INFO")
    try:
        f_silent = Fitter(data, distributions=["gamma", "norm"], verbose=False)
        f_silent.fit(prefer="threads")
    finally:
        logger.remove(handler_id)

    # verbose=True should log messages; verbose=False should log nothing
    assert len(verbose_messages) > 0
    assert len(silent_messages) == 0

    # Both modes should produce identical fit results
    assert set(f_verbose.fitted_param.keys()) == set(f_silent.fitted_param.keys())
    assert set(f_verbose.fitted_pdf.keys()) == set(f_silent.fitted_pdf.keys())
