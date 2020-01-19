

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

Another easy way to reduce the computational time is to provide a subset of your
data. If you date set has a length of 1 million data points, just sub-sample it
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

