FAQs
================

Why does it take so long ?
--------------------------

A typical fitter usage is as follows::

    from fitter import Fitter
    f = Fitter(data)
    f.fit()
    f.summary()

This will run the fitting process on your data with about 80 different
distributions. If you want to reduce the time significantly, provide a subset of
distributions as follows::

    from fitter import Fitter
    f = Fitter(data, distributions=["gamma", "rayleigh", "uniform"])
    f.fit()
    f.summary()

or use ``distributions="common"`` for a handful of common distributions. You can
also lower the ``timeout`` (in seconds) so that slow distributions are skipped
sooner.

Another easy way to reduce the computational time is to provide a subset of your
data. If your data set has a length of 1 million data points, just sub-sample it
to 10,000 points for instance. This way you can identify sensible distributions,
and try again with those distributions on the entire data (divide and conquer,
as always !)


What are the distributions available ?
---------------------------------------

Since version 1.2, you can use::

    from fitter import get_distributions
    get_distributions()

You may get a sub set of common distributions as follows::

    from fitter import get_common_distributions
    get_common_distributions()


Which metric should I use to choose the best distribution ?
-------------------------------------------------------------

The default ranking uses the sum of squared errors between the histogram and the
fitted PDF. You can rank with ``aic``, ``bic``, ``kl_div``, ``ks_statistic`` or
``ks_pvalue`` instead, e.g. ``f.summary(method="aic")`` or
``f.get_best(method="bic")``. All are ranked lowest first except ``ks_pvalue``
(highest first). See :doc:`tuto`.


I get a ValueError about unknown distributions
------------------------------------------------

The names given in ``distributions`` must match :mod:`scipy.stats` names
exactly (e.g. ``"norm"``, not ``"normal"``). Use ``fitter.get_distributions()`` to
list the valid names.


How do I silence the messages ?
-------------------------------

Use ``Fitter(data, verbose=False)``, or configure the ``"fitter"`` logger of the
standard :mod:`logging` module, e.g.
``logging.getLogger("fitter").setLevel(logging.ERROR)``. See :doc:`tuto`.


Why are some distributions missing from the summary or have infinite errors ?
-------------------------------------------------------------------------------

Distributions whose fit fails, exceeds the ``timeout`` or gives an invalid CDF
are skipped and get infinite errors, so they are ranked last.
