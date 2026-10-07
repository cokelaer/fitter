Examples
#############################

Basic usage
=================================================

Let us start with an example. We generate a vector of values from a gamma
distribution.

.. plot::
    :width: 80%
    :include-source:

    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=100000)

    from fitter import Fitter
    f = Fitter(data, distributions=['gamma', 'rayleigh', 'uniform'])
    f.fit()
    f.summary()

Here, we restrict the analysis to only 3 distributions by providing the list of
distributions to consider. If you do not provide that parameter, all the
distributions of SciPy that have a ``fit`` method are considered (about 80, see
:func:`fitter.fitter.get_distributions`); the analysis is then longer and may
take a while to finish.

The :meth:`fitter.fitter.Fitter.summary` method shows the best distributions (in
terms of fitting) as a :class:`pandas.DataFrame` and, by default, plots the
histogram of the data together with the fitted PDFs.

Choosing which distributions to fit
=================================================

The ``distributions`` argument accepts a list of names, a single name, or the
keyword ``"common"``::

    from fitter import Fitter, get_common_distributions

    Fitter(data, distributions=["gamma", "norm"])  # a list
    Fitter(data, distributions="gamma")            # a single distribution
    Fitter(data, distributions="common")           # a subset of common distributions
    get_common_distributions()                     # see what "common" contains

Names must be valid :mod:`scipy.stats` distributions. An unknown name raises a
:class:`ValueError` when the :class:`~fitter.fitter.Fitter` is created (not later
during the fit), which catches typos early::

    >>> Fitter(data, distributions=["gamma", "gama"])
    Traceback (most recent call last):
    ...
    ValueError: Unknown distribution(s): ['gama']. Use fitter.get_distributions() to list valid scipy.stats names.

Ranking with different metrics
=================================================

After :meth:`~fitter.fitter.Fitter.fit`, the attribute ``df_errors`` stores
several goodness-of-fit metrics for each distribution:

=================== =============================================================
Column              Meaning (ranking order)
=================== =============================================================
``sumsquare_error`` sum of squared differences between histogram and PDF (lowest)
``aic``             Akaike information criterion (lowest)
``bic``             Bayesian information criterion (lowest)
``kl_div``          Kullback-Leibler divergence (lowest)
``ks_statistic``    Kolmogorov-Smirnov statistic (lowest)
``ks_pvalue``       Kolmogorov-Smirnov p-value (**highest**)
=================== =============================================================

All metrics are ranked from best to worst, which means lowest first, except
``ks_pvalue`` for which a high p-value means that the data is compatible with the
fitted distribution, so the highest value comes first. The ``method`` argument of
:meth:`~fitter.fitter.Fitter.summary`, :meth:`~fitter.fitter.Fitter.plot_pdf` and
:meth:`~fitter.fitter.Fitter.get_best` selects the metric::

    from scipy import stats
    from fitter import Fitter

    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=5000)
    f = Fitter(data, distributions="common")
    f.fit()

    for method in ["sumsquare_error", "aic", "bic", "ks_statistic", "ks_pvalue"]:
        best = f.summary(Nbest=3, method=method, plot=False)
        print(method, list(best.index))

Different metrics may legitimately disagree, especially between close
candidates (here gamma and chi2, which are closely related). The default
``sumsquare_error`` compares the PDF to the histogram, so it depends on the
number of ``bins``; ``aic`` and ``bic`` are computed from the likelihood of the
raw data and penalise the number of parameters.

Trimming the data with xmin and xmax
=================================================

If your data has outliers or a very long tail, restrict the fit to a range with
``xmin`` and/or ``xmax``. Only the data within ``[xmin, xmax]`` is used for the
histogram and the fits. Increasing ``bins`` may also help::

    f = Fitter(data, xmin=2, xmax=10, bins=200, distributions=["gamma", "norm"])
    f.fit()
    f.summary(plot=False)

The attributes can be modified afterwards; set them back to ``None`` to use the
whole data set again.

Timeout and verbosity
=================================================

Some distributions converge very slowly. The ``timeout`` argument (in seconds,
30 by default) sets the maximum time spent on a given distribution; a
distribution that exceeds it is skipped and gets infinite errors. The ``verbose``
argument controls the log messages emitted while fitting::

    f = Fitter(data, distributions="common", timeout=10, verbose=False)
    f.fit(progress=True)   # show a progress bar instead

Controlling logging
=================================================

**fitter** uses the standard :mod:`logging` module with a logger named
``"fitter.fitter"`` (a child of the ``"fitter"`` logger). It does not configure any
handler itself, so nothing but warnings is displayed unless you set up logging.
To see the progress messages (one INFO line per fitted distribution)::

    import logging
    logging.basicConfig(level=logging.INFO)

To silence the library, or to redirect its messages to a file::

    import logging

    logging.getLogger("fitter").setLevel(logging.ERROR)   # silence warnings too

    handler = logging.FileHandler("fitter.log")
    logging.getLogger("fitter").addHandler(handler)

Setting ``verbose=False`` in the constructor is the simplest way to suppress the
messages.

.. note::

    The fits run in parallel. With the default ``prefer="processes"``, the worker
    processes do not inherit the logging configuration of your session, so the
    INFO messages may not appear. Use ``f.fit(prefer="threads")`` if you want to
    see them.

Using the best parameters with SciPy
=================================================

:meth:`~fitter.fitter.Fitter.get_best` returns a dictionary with the name of the
best distribution and its parameters, named according to SciPy's conventions
(shape parameters, ``loc`` and ``scale``). The keyword form can be used directly to
create a *frozen* SciPy distribution::

    >>> from scipy import stats
    >>> best = f.get_best(method="bic")
    >>> best
    {'gamma': {'a': 1.91, 'loc': 1.52, 'scale': 2.08}}

    >>> name, params = next(iter(best.items()))
    >>> dist = getattr(stats, name)(**params)
    >>> dist.ppf(0.5)    # median of the fitted distribution
    4.82
    >>> dist.cdf(5)      # probability that a value is below 5
    0.53
    >>> dist.rvs(size=3) # draw new samples from the fitted model

The raw parameters of any fitted distribution (not only the best one) are stored
as tuples in :attr:`~fitter.fitter.Fitter.fitted_param`::

    >>> f.fitted_param['gamma']
    (1.9870244799532322, 1.5026555566189543, 2.0174462493492964)

SciPy's documentation gives the meaning of each value for each distribution. The
fitted PDF evaluated at the bin centers is available in
``f.fitted_pdf['gamma']``. To draw the density yourself, use SciPy directly:

.. plot::
    :include-source:
    :width: 80%

    import numpy as np
    import matplotlib.pyplot as plt
    import scipy.stats

    dist = scipy.stats.gamma
    param = (1.9870, 1.5026, 2.0174)
    X = np.linspace(0, 20, 200)
    plt.plot(X, dist.pdf(X, *param), "-")

Saving the plot to a file
=================================================

:meth:`~fitter.fitter.Fitter.summary` draws on the current matplotlib figure, so
the usual matplotlib functions can be used to save it::

    import matplotlib.pyplot as plt

    f.summary(Nbest=3)
    plt.savefig("fit.png", dpi=200)

In a script without display, select a non-interactive backend first
(``import matplotlib; matplotlib.use("Agg")``).

HistFit class: fit the density function itself
=================================================

Sometimes, you only have the distribution itself. For instance::

        import scipy.stats
        from pylab import hist
        data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
        Y, X, _ = hist(data, bins=30)

here we have only access to Y (and X).

The histfit module provides the HistFit class to generate plots of your data
with a fitting curve based on several attempt at fitting your X/Y data with some
errors on the data set. For instance here below, we introduce 3% of errors and
fit the data 20 times to see if the fit makes sense.

.. plot::
    :include-source:
    :width: 80%

    from fitter import HistFit
    from pylab import hist
    import scipy.stats
    data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
    Y, X, _ = hist(data, bins=30)
    hf = HistFit(X=X, Y=Y)
    hf.fit(error_rate=0.03, Nfit=20)
    print(hf.mu, hf.sigma, hf.amplitude)
