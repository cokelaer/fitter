# -*- python -*-
# -*- coding: utf-8 -*-
#
#  This file is part of the fitter software
#
#  Copyright (c) 2014
#
#  File author(s): Thomas Cokelaer <cokelaer@gmail.com>
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  source: https://github.com/cokelaer/fitter
#  Documentation: http://packages.python.org/fitter
#  Package: http://pypi.python.org/fitter
#
##############################################################################
"""main module of the fitter package

.. sectionauthor:: Thomas Cokelaer, Aug 2014

"""
import sys
import threading
from datetime import datetime

import scipy.stats
import numpy as np
import pylab
import pandas as pd


class Fitter(object):
    """Fit a data sample to known distributions

    A naive approach often performed to figure out the undelying distribution that
    could have generated a data set, is to compare the histogram of the data with
    a PDF (probability distribution function) of a known distribution (e.g., normal).

    Yet, the parameters of the distribution are not known and there are lots of
    distributions. Therefore, an automatic way to fit many distributions to the data
    would be useful, which is what is implemented here.

    Given a data sample, we use the `fit` method of SciPy to extract the parameters
    of that distribution that best fit the data. We repeat this for all available distributions.
    Finally, we provide a summary so that one can see the quality of the fit for those distributions

    Here is an example where we generate a sample from a gamma distribution.

    ::

        >>> # First, we create a data sample following a Gamma distribution
        >>> from scipy import stats
        >>> data = stats.gamma.rvs(2, loc=1.5, scale=2, size=20000)

        >>> # We then create the Fitter object
        >>> import fitter
        >>> f = fitter.Fitter(data)

        >>> # just a trick to use only 10 distributions instead of 80 to speed up the fitting
        >>> f.distributions = f.distributions[0:10] + ['gamma']

        >>> # fit and plot
        >>> f.fit()
        >>> f.summary()
                sumsquare_error
        gamma          0.000095
        beta           0.000179
        chi            0.012247
        cauchy         0.044443
        anglit         0.051672
        [5 rows x 1 columns]

    Once the data has been fitted, the :meth:`summary` metod returns a sorted dataframe where the

    Looping over the 80 distributions in SciPy could takes some times so you can overwrite the
    :attr:`distributions` with a subset if you want. In order to reload all distributions,
    call :meth:`load_all_distributions`.

    Some distributions do not converge when fitting. There is a timeout of 10 seconds after which
    the fitting procedure is cancelled. You can change this :attr:`timeout` attribute if needed.

    If the histogram of the data has outlier of very long tails, you may want to increase the
    :attr:`bins` binning or to ignore data below or above a certain range. This can be achieved
    by setting the :attr:`xmin` and :attr:`xmax` attributes. If you set xmin, you can come back to
    the original data by setting xmin to None (same for xmax) or just recreate an instance.
    """

    def __init__(self, data, xmin=None, xmax=None, bins=100,
            distributions=None, verbose=True, timeout=10):
        """.. rubric:: Constructor

        :param list data: a numpy array or a list
        :param float xmin: if None, use the data minimum value, otherwise histogram and
            fits will be cut
        :param float xmax: if None, use the data maximum value, otherwise histogram and
            fits will be cut
        :param int bins: numbers of bins to be used for the cumulative histogram. This has
            an impact on the quality of the fit.
        :param list distributions: give a list of distributions to look at. IF none, use
            all scipy distributionsthat have a fit method.
        :param bool verbose:
        :param timeout: max time for a given distribution. If timeout is
            reached, the distribution is skipped.

        """
        self.timeout = timeout
        # USER input
        self._data = None

        #: list of distributions to test
        self.distributions = distributions
        if self.distributions == None:
            self.load_all_distributions()

        self.bins = bins
        self.verbose = verbose

        self._alldata = np.array(data)
        if xmin == None:
            self._xmin = self._alldata.min()
        else:
            self._xmin = xmin
        if xmax == None:
            self._xmax = self._alldata.max()
        else:
            self._xmax = xmax

        self._trim_data()
        self._update_data_pdf()

        # Other attributes
        self._init()

    def _init(self):
        self.fitted_param = {}
        self.fitted_pdf = {}
        self._fitted_errors = {}

    def _update_data_pdf(self):
        # histogram retuns X with N+1 values. So, we rearrange the X output into only N
        self.y, self.x = np.histogram(self._data, bins=self.bins, normed=True) # not to show
        self.x = [(this+self.x[i+1])/2. for i,this in enumerate(self.x[0:-1])]

    def _trim_data(self):
        self._data = self._alldata[np.logical_and(self._alldata >= self._xmin, self._alldata <= self._xmax)]

    def _get_xmin(self):
        return self._xmin
    def _set_xmin(self, value):
        if value == None:
            value = self._alldata.min()
        elif value < self._alldata.min():
            value = self._alldata.min()
        self._xmin = value
        self._trim_data()
        self._update_data_pdf()
    xmin = property(_get_xmin, _set_xmin, doc="consider only data above xmin. reset if None")

    def _get_xmax(self):
        return self._xmax
    def _set_xmax(self, value):
        if value == None:
            value = self._alldata.max()
        elif value > self._alldata.max():
            value = self._alldata.max()
        self._xmax = value
        self._trim_data()
        self._update_data_pdf()
    xmax = property(_get_xmax, _set_xmax, doc="consider only data below xmax. reset if None ")

    def load_all_distributions(self):
        """Replace the :attr:`distributions` attribute with all scipy distributions"""
        distributions = []
        for this in dir(scipy.stats):
            if "fit" in eval("dir(scipy.stats." + this +")"):
                distributions.append(this)
        self.distributions = distributions[:]

    def hist(self):
        """Draw normed histogram of the data using :attr:`bins`

        .. plot::

            >>> from scipy import stats
            >>> data = stats.gamma.rvs(2, loc=1.5, scale=2, size=20000)
            >>> # We then create the Fitter object
            >>> import fitter
            >>> fitter.Fitter(data).hist()


        """
        _ = pylab.hist(self._data, bins=self.bins, normed=True)
        pylab.grid(True)

    def fit(self):
        r"""Loop over distributions and find best parameter to fit the data for each

        When a distribution is fitted onto the data, we populate a set of
        dataframes:

            - :attr:`df_errors`  :sum of the square errors between the data and the fitted
              distribution i.e., :math:`\sum_i \left( Y_i - pdf(X_i) \right)^2`
            - :attr:`fitted_param` : the parameters that best fit the data
            - :attr:`fitted_pdf` : the PDF generated with the parameters that best fit the data

        Indices of the dataframes contains the name of the distribution.

        """
        for distribution in self.distributions:
            try:
                # need a subprocess to check time it takes. If too long, skip it
                dist = eval("scipy.stats." + distribution)

                # TODO here, dist.fit may take a while or just hang forever
                # with some distributions. So, I thought to use signal module
                # to catch the error when signal takes too long. It did not work
                # presumably because another try/exception is inside the
                # fit function, so I used threading with arecipe from stackoverflow
                # See timed_run function above
                param = self._timed_run(dist.fit, distribution, args=self._data)

                # with signal, does not work. maybe because another expection is caught
                pdf_fitted = dist.pdf(self.x, *param) # hoping the order returned by fit is the same as in pdf

                self.fitted_param[distribution] = param[:]
                self.fitted_pdf[distribution] = pdf_fitted

                sq_error = pylab.sum((self.fitted_pdf[distribution] - self.y)**2)
                if self.verbose:
                    print("Fitted {} distribution with error={})".format(distribution, sq_error))

                # compute some errors now
                self._fitted_errors[distribution] = sq_error
            except Exception as err:
                if self.verbose:
                    print("SKIPPED {} distribution (taking more than {} seconds)".format(distribution, 
                        self.timeout))
                # if we cannot compute the error, set it to large values
                # FIXME use inf
                self._fitted_errors[distribution] = 1e6

        self.df_errors = pd.DataFrame({'sumsquare_error':self._fitted_errors})

    def plot_pdf(self, names=None, Nbest=5, lw=2):
        """Plots Probability density functions of the distributions

        :param str,list names: names can be a single distribution name, or a list
            of distribution names, or kept as None, in which case, the first Nbest
            distribution will be taken (default to best 5)


        """
        assert Nbest>0
        if Nbest > len(self.distributions):
            Nbest = len(self.distributions)
        if isinstance(names, list):
            for name in names:
                pylab.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
        elif names:
            pylab.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
        else:
            try:
                names = self.df_errors.sort_values(
                        by="sumsquare_error").index[0:Nbest]
            except:
                names = self.df_errors.sort("sumsquare_error").index[0:Nbest]

            for name in names:
                if name in self.fitted_pdf.keys():
                    pylab.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
                else:
                    print("%s was not fitted. no parameters available" % name)
        pylab.grid(True)
        pylab.legend()

    def get_best(self):
        """Return best fitted distribution and its parameters

        a dictionary with one key (the distribution name) and its parameters

        """
        # self.df should be sorted, so then us take the first one as the best
        name = self.df_errors.sort('sumsquare_error').iloc[0].name
        params = self.fitted_param[name]
        return {name: params}

    def summary(self, Nbest=5, lw=2):
        """Plots the distribution of the data and Nbest distribution

        """
        pylab.clf()
        self.hist()
        self.plot_pdf(Nbest=Nbest, lw=lw)
        pylab.grid(True)

        Nbest = min(Nbest, len(self.distributions))
        try:
            names = self.df_errors.sort_values(
                    by="sumsquare_error").index[0:Nbest]
        except:
            names = self.df_errors.sort("sumsquare_error").index[0:Nbest]
        return self.df_errors.ix[names]

    def _timed_run(self, func, distribution, args=(), kwargs={},  default=None):
        """This function will spawn a thread and run the given function
        using the args, kwargs and return the given default value if the
        timeout is exceeded.

        http://stackoverflow.com/questions/492519/timeout-on-a-python-function-call
        """
        class InterruptableThread(threading.Thread):
            def __init__(self):
                threading.Thread.__init__(self)
                self.result = default
                self.exc_info = (None, None, None)

            def run(self):
                try:
                    self.result = func(args, **kwargs)
                except Exception as err:
                    self.exc_info = sys.exc_info()

            def suicide(self):
                raise RuntimeError('Stop has been called')

        it = InterruptableThread()
        it.start()
        started_at = datetime.now()
        it.join(self.timeout)
        ended_at = datetime.now()
        diff = ended_at - started_at

        if it.exc_info[0] is not None:  # if there were any exceptions
            a,b,c = it.exc_info
            raise Exception(a,b,c)  # communicate that to caller

        if it.isAlive():
            it.suicide()
            raise RuntimeError
        else:
            return it.result



""" For book-keeping

Another way to prevent a statement to run for a long time and to
stop it is to use the signal module but did not work with scipy presumably
because a try/except inside the distribution function interferes

def handler(signum, frame):
    raise Exception("end of time")

import signal
signal.signal(signal.SIGALRM, handler)
signal.alarm(timeout)

try:
    param = dist.fit(data)
except Exception as err:
    print(err.message)

"""
