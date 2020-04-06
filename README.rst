

#############################
FITTER documentation
#############################

.. image:: https://badge.fury.io/py/fitter.svg
    :target: https://pypi.python.org/pypi/fitter

.. image:: https://secure.travis-ci.org/cokelaer/fitter.png
    :target: http://travis-ci.org/cokelaer/fitter

.. image:: https://coveralls.io/repos/cokelaer/fitter/badge.png?branch=master 
    :target: https://coveralls.io/r/cokelaer/fitter?branch=master 

.. image:: http://readthedocs.org/projects/fitter/badge/?version=latest
    :target: http://fitter.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status


Compatible with Python 2.7 and 3.6 and 3.7 (Travis tests)


What is it ?
################

**fitter** package provides a simple class to identify the distribution from which a data samples is generated from. It uses 80 distributions from Scipy and allows you to plot the results to check what is the most probable distribution and the best parameters.


Installation
###################

::

    pip install fitter


Usage
##################


First, let us create a data samples with N = 10,000 points from a gamma distribution::

    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)

.. note:: the fitting is slow so keep the size value to reasonable value.

Now, without any knowledge about the distribution or its parameter, what is the distribution that fits the data best ? Scipy has 80 distributions and the **Fitter** class will scan all of them, call the fit function for you, ignoring those that fail or run forever and finally give you a summary of the best distributions in the sense of sum of the square errors. The best is to give an example::


    from fitter import Fitter
    f = Fitter(data)
    f.fit()
    # may take some time since by default, all distributions are tried
    # but you call manually provide a smaller set of distributions 
    f.summary()


.. image:: http://pythonhosted.org/fitter/_images/index-1.png
    :target: http://pythonhosted.org/fitter/_images/index-1.png


See the `online <http://fitter.readthedocs.io/>`_ documentation for details.





