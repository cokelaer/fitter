#  This file is part of the fitter software
#
#  Copyright (c) 2014-2022
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

.. sectionauthor:: Thomas Cokelaer, Aug 2014-2020

"""
import contextlib
import sys
import threading
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import pylab
import scipy.stats
from joblib.parallel import Parallel, delayed
from loguru import logger
from scipy.stats import entropy as kl_div
from scipy.stats import kstest
from tqdm import tqdm
import multiprocessing

__all__ = ["get_common_distributions", "get_distributions", "Fitter"]


# A solution to wrap joblib parallel call in tqdm from
# https://stackoverflow.com/questions/24983493/tracking-progress-of-joblib-parallel-execution/58936697#58936697
# and https://github.com/louisabraham/tqdm_joblib
@contextlib.contextmanager
def tqdm_joblib(*args, **kwargs):
    """Context manager to patch joblib to report into tqdm progress bar
    given as argument"""

    tqdm_object = tqdm(*args, **kwargs)

    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()


def get_distributions():
    distributions = []
    for this in dir(scipy.stats):
        if "fit" in eval("dir(scipy.stats." + this + ")"):
            distributions.append(this)
    return distributions


def get_common_distributions():
    distributions = get_distributions()
    # to avoid error due to changes in scipy
    common = [
        "cauchy",
        "chi2",
        "expon",
        "exponpow",
        "gamma",
        "lognorm",
        "norm",
        "powerlaw",
        "rayleigh",
        "uniform",
    ]
    common = [x for x in common if x in distributions]
    return common


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

                      sumsquare_error     aic            bic     kl_div  ks_statistic  ks_pvalue
        loggamma            0.001176  995.866732 -159536.164644     inf      0.008459   0.469031
        gennorm             0.001181  993.145832 -159489.437372     inf      0.006833   0.736164
        norm                0.001189  992.975187 -159427.247523     inf      0.007138   0.685416
        truncnorm           0.001189  996.975182 -159408.826771     inf      0.007138   0.685416
        crystalball         0.001189  996.975078 -159408.821960     inf      0.007138   0.685434

    Once the data has been fitted, the :meth:`summary` method returns a sorted dataframe where
    the index represents the distribution names.

    The AIC is computed using :math:`aic = 2 * k - 2 * log(Lik)`,
    and the BIC is computed as :math:`k * log(n) - 2 * log(Lik)`.


    where Lik is the maximized value of the likelihood function of the model,
    n the number of data point and k the number of parameter.

    Looping over the 80 distributions in SciPy could takes some times so you can overwrite the
    :attr:`distributions` with a subset if you want. In order to reload all distributions,
    call :meth:`load_all_distributions`.

    Some distributions do not converge when fitting. There is a timeout of 30 seconds after which
    the fitting procedure is cancelled. You can change this :attr:`timeout` attribute if needed.

    If the histogram of the data has outlier of very long tails, you may want to increase the
    :attr:`bins` binning or to ignore data below or above a certain range. This can be achieved
    by setting the :attr:`xmin` and :attr:`xmax` attributes. If you set xmin, you can come back to
    the original data by setting xmin to None (same for xmax) or just recreate an instance.
    """

    def __init__(
        self,
        data,
        xmin=None,
        xmax=None,
        bins=100,
        distributions=None,
        timeout=30,
        density=True,
    ):
        """.. rubric:: Constructor

        :param list data: a numpy array or a list
        :param float xmin: if None, use the data minimum value, otherwise histogram and
            fits will be cut
        :param float xmax: if None, use the data maximum value, otherwise histogram and
            fits will be cut
        :param int bins: numbers of bins to be used for the cumulative histogram. This has
            an impact on the quality of the fit.
        :param list distributions: give a list of distributions to look at. If none, use
            all scipy distributions that have a fit method. If you want to use
            only one distribution and know its name, you may provide a string (e.g.
            'gamma'). Finally, you may set to 'common' to  include only common
            distributions, which are: cauchy, chi2, expon, exponpow, gamma,
                 lognorm, norm, powerlaw, irayleigh, uniform.
        :param timeout: max time for a given distribution. If timeout is
            reached, the distribution is skipped.

        .. versionchanged:: 1.2.1 remove verbose argument, replacedb by logging module.
        .. versionchanged:: 1.0.8 increase timeout from 10 to 30 seconds.
        """
        self.timeout = timeout
        # USER input
        self._data = None

        # Issue https://github.com/cokelaer/fitter/issues/22 asked for setting
        # the density to False in the fitting and plotting. I first tought it
        # would be possible, but the fitting is performed using the PDF of scipy
        # so one would still need to normalise the data so that it is
        # comparable. Therefore I do not see anyway to do it without using
        # density set to True for now.
        self._density = True

        #: list of distributions to test
        self.distributions = distributions
        if self.distributions == None:
            self._load_all_distributions()
        elif self.distributions == "common":
            self.distributions = get_common_distributions()
        elif isinstance(distributions, str):
            self.distributions = [distributions]

        self.bins = bins

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
        self._aic = {}
        self._bic = {}
        self._kldiv = {}
        self._ks_stat = {}
        self._ks_pval = {}
        self._fit_i = 0  # fit progress
        # self.pb = None

    def _update_data_pdf(self):
        # histogram retuns X with N+1 values. So, we rearrange the X output into only N
        self.y, self.x = np.histogram(self._data, bins=self.bins, density=self._density)
        self.x = [(this + self.x[i + 1]) / 2.0 for i, this in enumerate(self.x[0:-1])]

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

    def _load_all_distributions(self):
        """Replace the :attr:`distributions` attribute with all scipy distributions"""
        self.distributions = get_distributions()

    def hist(self):
        """Draw normed histogram of the data using :attr:`bins`


        .. plot::

            >>> from scipy import stats
            >>> data = stats.gamma.rvs(2, loc=1.5, scale=2, size=20000)
            >>> # We then create the Fitter object
            >>> import fitter
            >>> fitter.Fitter(data).hist()

        """
        _ = pylab.hist(self._data, bins=self.bins, density=self._density)
        pylab.grid(True)

    @staticmethod
    def _fit_single_distribution(distribution, data, x, y, timeout):
        import warnings

        warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            # need a subprocess to check time it takes. If too long, skip it
            dist = eval("scipy.stats." + distribution)

            param = Fitter._with_timeout(dist.fit, args=(data,), timeout=timeout)

            # with signal, does not work. maybe because another expection is caught
            # hoping the order returned by fit is the same as in pdf
            pdf_fitted = dist.pdf(x, *param)

            # calculate error
            sq_error = pylab.sum((pdf_fitted - y) ** 2)

            # calculate information criteria
            logLik = np.sum(dist.logpdf(x, *param))
            k = len(param[:])
            n = len(data)
            aic = 2 * k - 2 * logLik

            # special case of gaussian distribution
            # bic = n * np.log(sq_error / n) + k * np.log(n)
            # general case:
            bic = k * pylab.log(n) - 2 * logLik

            # calculate kullback leibler divergence
            kullback_leibler = kl_div(pdf_fitted, y)

            # calculate goodness-of-fit statistic
            dist_fitted = dist(*param)
            ks_stat, ks_pval = kstest(data, dist_fitted.cdf)

            logger.info("Fitted {} distribution with error={})".format(distribution, round(sq_error, 6)))

            return distribution, (param, pdf_fitted, sq_error, aic, bic, kullback_leibler, ks_stat, ks_pval)
        except Exception:  # pragma: no cover
            logger.warning("SKIPPED {} distribution (taking more than {} seconds)".format(distribution, timeout))

            return distribution, None

    def fit(self, progress=False, n_jobs=-1, max_workers=-1, prefer="processes"):
        r"""Loop over distributions and find best parameter to fit the data for each

        When a distribution is fitted onto the data, we populate a set of
        dataframes:

            - :attr:`df_errors`  :sum of the square errors between the data and the fitted
              distribution i.e., :math:`\sum_i \left( Y_i - pdf(X_i) \right)^2`
            - :attr:`fitted_param` : the parameters that best fit the data
            - :attr:`fitted_pdf` : the PDF generated with the parameters that best fit the data

        Indices of the dataframes contains the name of the distribution.

        """
        N = len(self.distributions)
        with tqdm_joblib(desc=f"Fitting {N} distributions", total=N, disable=not progress) as progress_bar:
            results = Parallel(n_jobs=max_workers, prefer=prefer)(
                delayed(Fitter._fit_single_distribution)(dist, self._data, self.x, self.y, self.timeout) for dist in self.distributions
            )

        for distribution, values in results:
            if values is not None:
                param, pdf_fitted, sq_error, aic, bic, kullback_leibler, ks_stat, ks_pval = values

                self.fitted_param[distribution] = param
                self.fitted_pdf[distribution] = pdf_fitted
                self._fitted_errors[distribution] = sq_error
                self._aic[distribution] = aic
                self._bic[distribution] = bic
                self._kldiv[distribution] = kullback_leibler
                self._ks_stat[distribution] = ks_stat
                self._ks_pval[distribution] = ks_pval
            else:
                self._fitted_errors[distribution] = np.inf
                self._aic[distribution] = np.inf
                self._bic[distribution] = np.inf
                self._kldiv[distribution] = np.inf

        self.df_errors = pd.DataFrame(
            {
                "sumsquare_error": self._fitted_errors,
                "aic": self._aic,
                "bic": self._bic,
                "kl_div": self._kldiv,
                "ks_statistic": self._ks_stat,
                "ks_pvalue": self._ks_pval,
            }
        )
        self.df_errors.sort_index(inplace=True)

    def plot_pdf(self, names=None, Nbest=5, lw=2, method="sumsquare_error"):
        """Plots Probability density functions of the distributions

        :param str,list names: names can be a single distribution name, or a list
            of distribution names, or kept as None, in which case, the first Nbest
            distribution will be taken (default to best 5)


        """
        assert Nbest > 0
        if Nbest > len(self.distributions):
            Nbest = len(self.distributions)

        if isinstance(names, list):
            for name in names:
                pylab.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
        elif names:
            pylab.plot(self.x, self.fitted_pdf[names], lw=lw, label=names)
        else:
            try:
                names = self.df_errors.sort_values(by=method).index[0:Nbest]
            except Exception:
                names = self.df_errors.sort(method).index[0:Nbest]

            for name in names:
                if name in self.fitted_pdf.keys():
                    pylab.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
                else:  # pragma: no cover
                    logger.warning("%s was not fitted. no parameters available" % name)
        pylab.grid(True)
        pylab.legend()

    def get_best(self, method="sumsquare_error"):
        """Return best fitted distribution and its parameters

        a dictionary with one key (the distribution name) and its parameters

        """
        # self.df should be sorted, so then us take the first one as the best
        name = self.df_errors.sort_values(method).iloc[0].name
        params = self.fitted_param[name]
        distribution = getattr(scipy.stats, name)
        param_names = (distribution.shapes + ", loc, scale").split(", ") if distribution.shapes else ["loc", "scale"]

        param_dict = {}
        for d_key, d_val in zip(param_names, params):
            param_dict[d_key] = d_val
        return {name: param_dict}

    def summary(self, Nbest=5, lw=2, plot=True, method="sumsquare_error", clf=True):
        """Plots the distribution of the data and N best distributions"""
        if plot:
            if clf:
                pylab.clf()
            self.hist()
            self.plot_pdf(Nbest=Nbest, lw=lw, method=method)
            pylab.grid(True)

        Nbest = min(Nbest, len(self.distributions))
        try:
            names = self.df_errors.sort_values(by=method).index[0:Nbest]
        except:  # pragma: no cover
            names = self.df_errors.sort(method).index[0:Nbest]
        return self.df_errors.loc[names]

    @staticmethod
    def _with_timeout(func, args=(), kwargs={}, timeout=30):
        with multiprocessing.pool.ThreadPool(1) as pool:
            async_result = pool.apply_async(func, args, kwargs)
            return async_result.get(timeout=timeout)


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
