

#############################
FITTER documentation
#############################

.. image:: https://badge.fury.io/py/fitter.svg
    :target: https://pypi.python.org/pypi/fitter

.. image:: https://github.com/cokelaer/fitter/actions/workflows/main.yml/badge.svg?branch=main
    :target: https://github.com/cokelaer/fitter/actions/workflows/main.yml

.. image:: https://coveralls.io/repos/cokelaer/fitter/badge.png?branch=main
    :target: https://coveralls.io/r/cokelaer/fitter?branch=main

.. image:: http://readthedocs.org/projects/fitter/badge/?version=latest
    :target: http://fitter.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/23078551.svg
   :target: https://zenodo.org/badge/latestdoi/23078551

Compatible with Python 3.7, and 3.8, 3.9


What is it ?
################

The **fitter** package is a Python library used for fitting probability distributions to data. It provides a straightforward and and intuitive interface to estimate parameters for various types of distributions, both continuous and discrete. Using **fitter**, you can easily fit a range of distributions to your data and compare their fit, aiding in the selection of the most suitable distribution. The package is designed to be user-friendly and requires minimal setup, making it a useful tool for data scientists and statisticians working with probability distributions.

Installation
###################

::

    pip install fitter

**fitter** is also available on **conda** (bioconda channel)::

     conda install fitter


Usage
##################

standalone
===========

A standalone application (very simple) is also provided and works with input CSV
files::

    fitter fitdist data.csv --column-number 1 --distributions gamma,normal

It creates a file called fitter.png and a log fitter.log

From Python shell
==================

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


Contributors
=============


Setting up and maintaining Fitter has been possible thanks to users and contributors.
Thanks to all:

.. image:: https://contrib.rocks/image?repo=cokelaer/fitter
    :target: https://github.com/cokelaer/fitter/graphs/contributors




Changelog
~~~~~~~~~
========= ==========================================================================
Version   Description
========= ==========================================================================
1.7.1     * integrate PR github.com/cokelaer/fitter/pull/100 from @vitorandreazza
            to speedup multiprocessing run.
1.7.0     * replace logging with loguru
          * main application update to add missing --output-image option and use
            rich_click
          * replace pkg_resources with importlib
1.6.0     * for developers: uses pyproject.toml instead of setup.py
          * Fix progress bar fixing https://github.com/cokelaer/fitter/pull/74
          * Fix BIC formula https://github.com/cokelaer/fitter/pull/77
1.5.2     * PR https://github.com/cokelaer/fitter/pull/74 to fix logger
1.5.1     * fixed regression putting back joblib
1.5.0     * removed easydev and replaced by tqdm for progress bar
          * progressbar from tqdm also allows replacement of joblib need
1.4.1     * Update timeout in docs from 10 to 30 seconds by @mpadge in
            https://github.com/cokelaer/fitter/pull/47
          * Add Kolmogorov-Smirnov goodness-of-fit statistic by @lahdjirayhan in
            https://github.com/cokelaer/fitter/pull/58
          * switch branch from master to main
1.4.0     * get_best function now returns the parameters as a dictionary
            of parameter names and their values rather than just a list of
            values (https://github.com/cokelaer/fitter/issues/23) thanks to
            contributor @kabirmdasraful
          * Accepting PR to fix progress bar issue reported in
            https://github.com/cokelaer/fitter/pull/37
1.3.0     * parallel process implemented https://github.com/cokelaer/fitter/pull/25
            thanks to @arsenyinfo
1.2.3     * remove vervose arguments in Fitter class. Using the logging module
            instead
          * the Fitter.fit has now a progress bar
          * add a standalone application called … fitter (see the doc)
1.2.2     was not released
1.2.1     adding new class called histfit (see documentation)
1.2       * Fixed the version. Previous version switched from
            1.0.9 to 1.1.11. To start a fresh version, we increase to 1.2.0
          * Merged pull request required by bioconda
          * Merged pull request related to implementation of
            AIC/BIC/KL criteria (https://github.com/cokelaer/fitter/pull/19).
            This also fixes https://github.com/cokelaer/fitter/issues/9
          * Implement two functions to get all distributions, or a list of
            common distributions to help users decreading computational time
            (https://github.com/cokelaer/fitter/issues/20). Also added a FAQS
            section.
          * travis tested Python 3.6 and 3.7 (not 3.5 anymore)
1.1       * Fixed deprecated warning
          * fitter is now in readthedocs at fitter.readthedocs.io
1.0.9     * https://github.com/cokelaer/fitter/pull/8 and 11
            PR https://github.com/cokelaer/fitter/pull/8
1.0.6     * summary() now returns the dataframe (instead of printing it)
1.0.5      https://github.com/cokelaer/fitter/issues
1.0.2     add manifest to fix missing source in the pypi repository.
========= ==========================================================================
