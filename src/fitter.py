# -*- python -*-
# -*- coding: utf-8 -*-
#
#  This file is part of the easydev software
#  It is a modified version of console.py from the sphinx software
#
#  Copyright (c) 2011-2014
#
#  File author(s): Thomas Cokelaer <cokelaer@gmail.com>
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: https://www.assembla.com/spaces/pyeasydev/wiki
#  Documentation: http://packages.python.org/easydev
#
##############################################################################
import sys
import threading
from datetime import datetime

import scipy.stats
import numpy as np
import pylab
import pandas as pd


class Fitter(object):
    """Given a list of distribution, fit them to a data sample.


    ::

        >>> from scipy import stats
        >>> data = stats.gamma.rvs(2, loc=1.5, scale=2, size=20000)
        >>> import fitter

        >>> f = fitter.Fitter(data)
        >>> f.distributions = f.distributions[0:10] + ['gamma']
        >>> f.fit()
        >>> f.summary()
                sumsquare_error
        gamma          0.000095
        beta           0.000179
        chi            0.012247
        cauchy         0.044443
        anglit         0.051672
        [5 rows x 1 columns]



    """

    def __init__(self, data, xmin=None, xmax=None, bins=100, distributions=None, verbose=True):
        """

        :param list data:
        :param float xmin: if None, use the data, otherwise histogram and 
            fits will be cut
        :param float xmax: if None, use the data, otherwise histogram and 
            fits will be cut
        :param int bins:
        :param list distributions:
        :param bool verbose:

        """
        self.timeout = 10
        # USER input
        self._data = None

        if distributions == None:
            self.load_all_distributions()
        else:
            self.distributions = distributions[:]

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
            self._xmax = self._alldata.max()

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
        """Replaces the :attr:`distributions` attribute with all scipy distributions"""
        distributions = []
        for this in dir(scipy.stats):
            if "fit" in eval("dir(scipy.stats." + this +")"):
                distributions.append(this)
        self.distributions = distributions[:]
    
    def hist_data(self):
        """Draw normed histogram of the data using :attribute:`bins`"""
        _ = pylab.hist(self._data, bins=self.bins, normed=True)
        pylab.grid(True)


    def fit(self, fitall=True):
        """Loop over distribution and find best parameter to fit the data for each 
        
        :param bool fitall: True means restart from scratch replacing existing results

        Fills attributes :attr:`df_errors`, :attr:`fitted_pdf`,
        and :attr:`fitted_pdf`

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
                param = self.timed_run(dist.fit, args=self._data)

                # with signal, does not work. maybe because another expection is caught 

                pdf_fitted = dist.pdf(self.x, *param) # hoping the order returned by fit is the same as in pdf

                self.fitted_param[distribution] = param[:]
                self.fitted_pdf[distribution] = pdf_fitted

                sq_error = pylab.sum((self.fitted_pdf[distribution] -
                    self.y)**2)
                print("Searching best parameters for distribution {} (error {})".format(distribution, sq_error))

                # compute some errors now
                self._fitted_errors[distribution] = sq_error
            except Exception as err:
                print(err.message)
                print("SKIPPED {} distribution (taking more than {} seconds)".format(distribution, self.timeout))


        self.df_errors = pd.DataFrame({'sumsquare_error':self._fitted_errors})

    def plot_pdf(self, names=None, Nbest=5):
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
                pylab.plot(self.x, self.fitted_pdf[name], lw=2, label=name)
        elif names:
            pylab.plot(self.x, self.fitted_pdf[name], lw=2, label=name)
        else:
            names = self.df_errors.sort("sumsquare_error").index[0:Nbest]
            for name in names:
                pylab.plot(self.x, self.fitted_pdf[name], lw=2, label=name)
        pylab.grid(True)
        pylab.legend()

    def summary(self, Nbest=5):
        """Plots the distribution of the data and Nbest distribution

        """
        pylab.clf()
        self.hist_data()
        self.plot_pdf()
        pylab.grid(True)

        Nbest = min(Nbest, len(self.distributions))
        names = self.df_errors.sort("sumsquare_error").index[0:Nbest]
        print(self.df_errors.ix[names])

    def timed_run(self, func, args=(), kwargs={}, timeout=10, default=None):
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
                except Exception as e:
                    self.exc_info = sys.exc_info()
    
            def suicide(self):
                raise RuntimeError('Stop has been called')
    
        it = InterruptableThread()
        it.start()
        # print("calling %(func)r for %(timeout)r seconds" % locals())
        started_at = datetime.now()
        it.join(self.timeout)
        ended_at = datetime.now()
        diff = ended_at - started_at
        # print("%(f)s exited after %(d)r seconds" % {'f': func, 'd': diff.seconds})
        if it.exc_info[0] is not None:  # if there were any exceptions
            a,b,c = it.exc_info
            raise a,b,c  # communicate that to caller
        if it.isAlive():
            it.suicide()
            raise RuntimeError("%(f)s timed out after %(d)r seconds" % 
                    {'f': func, 'd': diff.seconds})
        else:
            return it.result



""" Another way to prevent a statement to run for a long time and to 
stop it is to use the signal module but did not work with scipy presumably
because a try/except inside the distribution function interferes


def handler(signum, frame):
    raise Exception("end of time")

import signal
signal.signal(signal.SIGALRM, handler)
signal.alarm(timeout)


try:
    param = dist.fitdata)
except Exception as err:
    print(err.message)

"""
