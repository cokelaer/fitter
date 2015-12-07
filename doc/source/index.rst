

#############################
FITTER documentation
#############################

**fitter** package provides a simple class to figure out from whih distribution your data comes from. It uses scipy package to try 80 distributions and allows you to plot the results to check what is the most probable distribution.


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


Now, the question without any knowledge about the distribution of its parameter, what is a probable distributions that fit the data? scipy has 80 distribution with a method called **fit** that will help us here. The :class:`fitter.Fitter` will scan all the scipy distributions, call the fit function for you, ignoring those that fail or run forever and finally it will give you a summary of the best distributions in the sense of sum of the square errors. The best is to give an example:


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
distributions to considered. If you do not provide that parameter, 80
distributions will be considered (the analysis will be longer).


The :meth:`fitter.Fitter.summary` method shows the first best distributions (in
terms of fitting). 

Once the fitting is performed, one may want to get the parameters 
corresponding to the best distribution. The
parameters are stored in :attr:`fitted_param`. For instance in the example
above, the summary told us that the Gamma distribution has the best fit. You 
would retrieve the parameters of the Gamma distribution as follows::

    >>> f.fitted_param['gamma']
    (1.9870244799532322, 1.5026555566189543, 2.0174462493492964)

Here, you will need to look at scipy documentation to figure out what are those
parameters (mean, sigma, shape, ...). For convenience, we  do provide the corresponding PDF::
    
    f.fitted_pdf['gamma']

but you may want to plot the gamma distribution yourself. In that case, you will need to use Scipy package itself. Here is an example 

.. plot::
    :include-source:
    :width: 80%

    from pylab import linspace, plot
    import scipy.stats
    
    dist = scipy.stats.gamma
    param = (1.9870, 1.5026, 2.0174)
    X = linspace(0,10, 10)
    pdf_fitted = dist.pdf(X, *param)
    plot(X, pdf_fitted, 'o')





Reference Guide
##################


.. toctree::
    :maxdepth: 2
    :numbered:

    references
    contrib
