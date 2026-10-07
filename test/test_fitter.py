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


def test_verbose(caplog):
    """Test that verbose=False suppresses log output without affecting fit results."""
    import logging

    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)

    # Use prefer="threads" so logging happens in the same process and can be captured.
    with caplog.at_level(logging.INFO, logger="fitter"):
        f_verbose = Fitter(data, distributions=["gamma", "norm"], verbose=True)
        f_verbose.fit(prefer="threads")
    verbose_messages = list(caplog.records)
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="fitter"):
        f_silent = Fitter(data, distributions=["gamma", "norm"], verbose=False)
        f_silent.fit(prefer="threads")
    silent_messages = list(caplog.records)

    # verbose=True should log messages; verbose=False should log nothing
    assert len(verbose_messages) > 0
    assert len(silent_messages) == 0

    # Both modes should produce identical fit results
    assert set(f_verbose.fitted_param.keys()) == set(f_silent.fitted_param.keys())
    assert set(f_verbose.fitted_pdf.keys()) == set(f_silent.fitted_pdf.keys())


def test_cdf_bounds_validation():
    """Test that distributions with CDF values outside [0, 1] are skipped.

    Regression test for: geninvgauss can produce CDF > 1 for certain fitted
    parameters, which indicates a numerically invalid fit and should be
    excluded from results.
    """
    import scipy.stats

    # These geninvgauss parameters are known to produce CDF > 1
    params = (
        0.48753085620446013,
        5.181675881089951e-11,
        0.00015499999999999997,
        2.953504104288843e-14,
    )
    dist = scipy.stats.geninvgauss
    # Confirm the known bad CDF value that triggered the issue (CDF at x=0.05 > 1)
    assert dist.cdf(0.05, *params) > 1, "Test precondition: CDF should be > 1 for these params"

    # Create a dataset using these problematic parameters; use fixed seed for reproducibility
    data = dist.rvs(*params, size=200, random_state=42)

    # Fit only geninvgauss and check the result
    f = Fitter(data, distributions=["geninvgauss"])
    f.fit()

    # If geninvgauss was skipped due to invalid CDF, it won't be in fitted_param
    # If it was fitted successfully, its CDF must be valid (within [0, 1])
    if "geninvgauss" in f.fitted_param:
        fitted_params = f.fitted_param["geninvgauss"]
        fitted_dist = dist(*fitted_params)
        import numpy as np

        cdf_at_data = fitted_dist.cdf(data)
        assert np.all(cdf_at_data <= 1), "Fitted geninvgauss CDF must not exceed 1"
        assert np.all(cdf_at_data >= 0), "Fitted geninvgauss CDF must not be below 0"


def test_unknown_distribution_raises():
    import pytest

    with pytest.raises(ValueError, match="normal"):
        Fitter([1, 2, 3, 4, 5], distributions=["gamma", "normal"])


def test_get_best_ks_pvalue_is_highest():
    from scipy import stats

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)
    f = Fitter(data, distributions=["gamma", "norm", "uniform"])
    f.fit(prefer="threads")
    best = next(iter(f.get_best(method="ks_pvalue")))
    assert f.df_errors.loc[best, "ks_pvalue"] == f.df_errors["ks_pvalue"].max()
    assert f.summary(plot=False, method="ks_pvalue").index[0] == best


def _gamma_data(size=1000):
    from scipy import stats

    return stats.gamma.rvs(2, loc=1.5, scale=2, size=size)


def test_plot_pdf_names():
    import matplotlib

    matplotlib.use("Agg")
    f = Fitter(_gamma_data(), distributions=["gamma", "norm"])
    f.fit(prefer="threads")
    f.plot_pdf(names="gamma")
    f.plot_pdf(names=["gamma", "norm"])
    # unknown names only log a warning
    f.plot_pdf(names="not_fitted")
    f.plot_pdf(names=["gamma", "not_fitted"])
    f.plot_pdf(Nbest=1, method="ks_pvalue")


def test_get_best_without_shape_parameters():
    f = Fitter(_gamma_data(), distributions=["norm"])
    f.fit(prefer="threads")
    best = f.get_best()
    assert list(best) == ["norm"]
    assert set(best["norm"]) == {"loc", "scale"}


def test_failed_fit_gets_infinite_error(monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError("too slow")

    monkeypatch.setattr(Fitter, "_with_timeout", staticmethod(fail))
    f = Fitter(_gamma_data(), distributions=["gamma"])
    f.fit(prefer="threads")
    assert f.fitted_param == {}
    row = f.df_errors.loc["gamma"]
    assert row["sumsquare_error"] == float("inf")
    assert row["ks_pvalue"] == 0.0


def test_invalid_cdf_is_skipped(monkeypatch):
    import numpy as np
    import scipy.stats

    class Frozen:
        def cdf(self, x):
            return np.full_like(np.asarray(x, dtype=float), 2.0)

    class BadDist:
        @staticmethod
        def fit(data):
            return (0.0, 1.0)

        @staticmethod
        def pdf(x, *params):
            return np.ones_like(x)

        @staticmethod
        def logpdf(x, *params):
            return np.zeros_like(x)

        def __new__(cls, *params):
            return Frozen()

    monkeypatch.setattr(scipy.stats, "bad_dist", BadDist, raising=False)
    f = Fitter(_gamma_data(), distributions=["bad_dist"])
    f.fit(prefer="threads")
    assert "bad_dist" not in f.fitted_param
    assert f.df_errors.loc["bad_dist", "sumsquare_error"] == float("inf")
