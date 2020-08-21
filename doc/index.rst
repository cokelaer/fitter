

#############################
FITTER documentation
#############################


.. raw:: html

     <div style="width:80%"><p>
     <a href="https://pypi.python.org/pypi/fitter">
     <img src="https://badge.fury.io/py/fitter.svg"></a>

     <a href="https://travis-ci.org/cokelaer/fitter">
     <img src="https://travis-ci.org/cokelaer/fitter.png"></a>

     <a href="https://coveralls.io/r/cokelaer/fitter?branch=master">
     <img src="https://coveralls.io/repos/cokelaer/fitter/badge.png?branch=master"></a>

    <a href="https://fitter.readthedocs.org/">
    <img src="https://readthedocs.org/projects/fitter/badge/?version=latest"></a>


     </p>
     </div>





Compatible with Python 2.7, 3.6 and 3.7 (Travis tests)


What is it ?
################

**fitter** package provides a simple class to identify the distribution from which a data samples is generated from. It uses 80 distributions from Scipy and allows you to plot the results to check what is the most probable distribution and the best parameters.


A common tasks in data science or statistics it is identify the underlying
distribution from which your data comes from. Usually, an histogram can give you
a good idea but there are many distributions in real life. The **fitter** package 
provides a simple class to figure out from which distribution your data comes from. 


Installation
###################

**fitter** is a Python package available on Pypi website. It can be installed
with Python using the **pip** executable::

    pip install fitter

**fitter** is also available on **conda** (bioconda channel)::

    conda install fitter




Usage
##################

Standalone
==========

A standalone application (very simple) is also provided and works with input CSV
files::
 
    fitter fitdist data.csv --column-number 1 --distributions gamma,normal

It creates a file called fitter.png and a log fitter.log



Fitter class: find the underlying distribution
==============================================
Nothing complicated since there is just one class provided. First, we will need to create some data samples. Let us create
a sequence of 100000 samples from a gamma distribution::

    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=100000)


Now, we may ask ourself (without any knowledge about the distribution or its parameter) what is the most probable distribution that fits the data best ? Scipy package has 80 distributions, each of them has a method called **fit** that will help us here. The :class:`~fitter.fitter.Fitter` will first scan all the scipy distributions, then calls the fit function for you, ignoring those that fail or run forever and finally it will give you a summary of the best distributions in the sense of sum of the square errors. Here is an example:


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
distributions to consider. If you do not provide that parameter, 80
distributions will be considered (the analysis will be longer) and computation
make take a while to finish.


The :meth:`fitter.fitter.Fitter.summary` method shows the first best distributions (in
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
    plot(X, pdf_fitted, 'o-')


HistFit class: fit the density function itself
=================================================

Sometimes, you only have the distriution itself. For instance::

        import scipy.stats
        data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
        Y, X, _ = hist(data, bins=30)

here we have only access to Y (and X).

The histfit module provides the HistFit class to generate plots of your data
with a fitting curve based on several attempt at fitting your X/Y data with some
errors on the data set. For instance here below, we introduce 3% of errors and
fit the data 20 times to see if the fit makes sense.
 
.. plot::

    from fitter import HistFit
    from pylab import hist
    import scipy.stats
    data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
    Y, X, _ = hist(data, bins=30)
    hf = HistFit(X=X, Y=Y)
    hf.fit(error_rate=0.03, Nfit=20)
    print(hf.mu, hf.sigma, hf.amplitude)






Documentation
#############

.. toctree::
    :maxdepth: 2

    faqs
    references
    history
    contrib
