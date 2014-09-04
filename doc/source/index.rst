

#############################
FITTER documentation
#############################

**fitter** package provides a simple class to figure out from whih distribution your data comes from. It uses scipy package to try 80 ditributions and allows you to plot the results to check what is the most probable distribution.


Installation
###################

::

    pip install fitter


Usage
##################

Nothing complicated since there is just one class provided. First, we will need to create some data samples. Let us create
a sequence of 100000 samples from a gamma distribution::

    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=100000)


Now, the question without any knowledge about the distribution of its parameter, what is a probable distribution that fit the data? scipy has 80 distribution with a method called **fit** that will help us here. The :class:`fitter.Fitter` will scan all the distribution, call the fit function for you, ignoring those that fail or run forever and finally give you a summary of the best distribution in the sense of sum of the square errors. The best is to give an example::


    from fitter import Fitter
    f = Fitter(data)
    f.fit()
    # make take some time since by default, all distribution are tried
    f.summary()

.. plot::
    :width: 80%

    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=100000)
    from fitter import Fitter
    f = Fitter(data, distributions=['gamma', 'rayleigh', 'uniform'])
    f.fit()
    f.summary()



Reference Guide
##################


.. toctree::
    :maxdepth: 2
    :numbered:

    references
    contrib
