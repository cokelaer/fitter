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
"""Main module of the fitter package.

This module provides the Fitter class for fitting multiple probability distributions
to data samples and comparing their goodness of fit using various metrics.

.. sectionauthor:: Thomas Cokelaer, Aug 2014-2020
"""

from __future__ import annotations

import contextlib
import multiprocessing
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy.stats
from joblib.parallel import Parallel, delayed
from loguru import logger
from matplotlib import pyplot as plt
from scipy.stats import entropy as kl_div
from scipy.stats import kstest
from tqdm import tqdm

__all__ = ["Fitter", "get_common_distributions", "get_distributions"]


# A solution to wrap joblib parallel call in tqdm from
# https://stackoverflow.com/questions/24983493/tracking-progress-of-joblib-parallel-execution/58936697#58936697
# and https://github.com/louisabraham/tqdm_joblib
@contextlib.contextmanager
def tqdm_joblib(*args: Any, **kwargs: Any) -> Any:
    """Context manager to patch joblib to report into tqdm progress bar.

    Args:
        *args: Positional arguments passed to tqdm.
        **kwargs: Keyword arguments passed to tqdm.

    Yields:
        tqdm object for progress tracking.

    """
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


def get_distributions() -> list[str]:
    """Get all scipy.stats distributions that have a fit method.

    Returns:
        List of distribution names as strings.

    """
    # BUGFIX: Replace eval() with getattr() - safer and faster
    distributions = [
        name for name in dir(scipy.stats)
        if hasattr(getattr(scipy.stats, name, None), 'fit')
    ]
    return distributions


def get_common_distributions() -> list[str]:
    """Get commonly used distributions that are available in scipy.stats.

    Returns:
        List of common distribution names that have fit methods.

    Note:
        Filters based on scipy version to avoid errors with missing distributions.

    """
    distributions = get_distributions()
    # Convert to set for O(1) lookup (much faster than list membership)
    dist_set = set(distributions)
    # Common distributions to avoid error due to changes in scipy
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
    # Single-pass filter with set lookup (O(n) instead of O(n²))
    return [x for x in common if x in dist_set]


class Fitter:
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
        data: np.ndarray | list[float],
        xmin: float | None = None,
        xmax: float | None = None,
        bins: int = 100,
        distributions: list[str] | str | None = None,
        timeout: int = 30,
        density: bool = True,
        verbose: bool = True,
    ) -> None:
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
        :param bool verbose: if True (default), log fitting progress messages. Set to
            False to suppress all informational output.

        .. versionchanged:: 1.3.0 re-add verbose argument to allow suppressing log output.
        .. versionchanged:: 1.0.8 increase timeout from 10 to 30 seconds.
        """
        self.verbose = verbose
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
        self.distributions: list[str]
        if distributions is None:
            self._load_all_distributions()
        elif distributions == "common":
            self.distributions = get_common_distributions()
        elif isinstance(distributions, str):
            self.distributions = [distributions]
        else:
            self.distributions = distributions

        self.bins = bins

        self._alldata: np.ndarray = np.asarray(data)
        # Use ternary for cleaner code
        self._xmin: float = self._alldata.min() if xmin is None else xmin
        self._xmax: float = self._alldata.max() if xmax is None else xmax

        self._trim_data()
        self._update_data_pdf()

        # Other attributes
        self._init()

    def _init(self) -> None:
        """Initialize result storage dictionaries."""
        self.fitted_param: dict[str, tuple] = {}
        self.fitted_pdf: dict[str, np.ndarray] = {}
        self._fitted_errors: dict[str, float] = {}
        self._aic: dict[str, float] = {}
        self._bic: dict[str, float] = {}
        self._kldiv: dict[str, float] = {}
        self._ks_stat: dict[str, float] = {}
        self._ks_pval: dict[str, float] = {}
        self._fit_i: int = 0  # fit progress

    def _update_data_pdf(self) -> None:
        """Compute histogram of data and convert bin edges to bin centers.

        Note:
            np.histogram returns N+1 bin edges for N bins. We convert to N bin centers.

        """
        self.y: np.ndarray
        self.x: np.ndarray
        self.y, bin_edges = np.histogram(self._data, bins=self.bins, density=self._density)
        # OPTIMIZATION: Vectorized bin center calculation (much faster than list comprehension)
        self.x = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    def _trim_data(self) -> None:
        """Filter data to be within [xmin, xmax] range."""
        # Vectorized boolean indexing (efficient)
        self._data: np.ndarray = self._alldata[
            (self._alldata >= self._xmin) & (self._alldata <= self._xmax)
        ]

    def _get_xmin(self) -> float:
        """Get the minimum x value for data filtering."""
        return self._xmin

    def _set_xmin(self, value: float | None) -> None:
        """Set the minimum x value for data filtering."""
        if value is None or value < self._alldata.min():
            value = self._alldata.min()
        self._xmin = value
        self._trim_data()
        self._update_data_pdf()

    xmin = property(_get_xmin, _set_xmin, doc="consider only data above xmin. reset if None")

    def _get_xmax(self) -> float:
        """Get the maximum x value for data filtering."""
        return self._xmax

    def _set_xmax(self, value: float | None) -> None:
        """Set the maximum x value for data filtering."""
        if value is None or value > self._alldata.max():
            value = self._alldata.max()
        self._xmax = value
        self._trim_data()
        self._update_data_pdf()

    xmax = property(_get_xmax, _set_xmax, doc="consider only data below xmax. reset if None")

    def _load_all_distributions(self) -> None:
        """Replace the :attr:`distributions` attribute with all scipy distributions."""
        self.distributions = get_distributions()

    def hist(self) -> None:
        """Draw normalized histogram of the data using :attr:`bins`.

        Examples:
            >>> from scipy import stats
            >>> data = stats.gamma.rvs(2, loc=1.5, scale=2, size=20000)
            >>> import fitter
            >>> fitter.Fitter(data).hist()

        """
        plt.hist(self._data, bins=self.bins, density=self._density)
        plt.grid(True)

    @staticmethod
    def _fit_single_distribution(
        distribution: str,
        data: np.ndarray,
        x: np.ndarray,
        y: np.ndarray,
        timeout: int,
        verbose: bool = True,
    ) -> tuple[str, tuple | None]:
        """Fit a single distribution to data and compute goodness-of-fit metrics.

        Args:
            distribution: Name of the scipy.stats distribution to fit.
            data: Raw data array to fit.
            x: Bin centers for histogram comparison.
            y: Histogram density values.
            timeout: Maximum time allowed for fitting (seconds).
            verbose: If True, log fitting progress messages.

        Returns:
            Tuple of (distribution_name, results_tuple) where results_tuple contains
            (params, pdf_fitted, sq_error, aic, bic, kl_div, ks_stat, ks_pval)
            or None if fitting failed.

        """
        import warnings

        warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            # BUGFIX: Replace eval() with getattr() - safer and faster
            dist = getattr(scipy.stats, distribution)

            param = Fitter._with_timeout(dist.fit, args=(data,), timeout=timeout)

            # Compute PDF at bin centers for visualization
            pdf_fitted = dist.pdf(x, *param)

            # Calculate sum of squared errors between fitted PDF and histogram
            sq_error = np.sum((pdf_fitted - y) ** 2)

            # CRITICAL BUGFIX: logLik should be computed on DATA, not bin centers
            # Original used x (bins) which gives wrong likelihood
            logLik = np.sum(dist.logpdf(data, *param))
            k = len(param)  # Number of parameters
            n = len(data)   # Number of data points
            
            # Akaike Information Criterion: AIC = 2k - 2*ln(L)
            aic = 2 * k - 2 * logLik

            # Bayesian Information Criterion: BIC = k*ln(n) - 2*ln(L)
            bic = k * np.log(n) - 2 * logLik

            # Calculate Kullback-Leibler divergence (requires positive values)
            # Add small epsilon to avoid log(0) issues
            eps = 1e-10
            kullback_leibler = kl_div(pdf_fitted + eps, y + eps)

            # Create frozen distribution for efficient CDF evaluation
            dist_fitted = dist(*param)

            # Validate that the CDF is bounded within [0, 1] over the data range.
            # Some distributions (e.g. geninvgauss) can return CDF values slightly
            # above 1 due to numerical issues, which indicates an invalid fit.
            cdf_values = dist_fitted.cdf(x)
            if np.any(cdf_values > 1) or np.any(cdf_values < 0):
                if verbose:
                    logger.warning(
                        f"SKIPPED {distribution}: CDF values outside [0, 1] "
                        f"(min={cdf_values.min():.6g}, max={cdf_values.max():.6g})"
                    )
                return distribution, None

            # Calculate Kolmogorov-Smirnov goodness-of-fit statistic
            ks_stat, ks_pval = kstest(data, dist_fitted.cdf)

            if verbose:
                logger.info(
                    f"Fitted {distribution}: error={sq_error:.6f}, "
                    f"AIC={aic:.2f}, KS={ks_stat:.4f}"
                )

            return distribution, (
                param,
                pdf_fitted,
                sq_error,
                aic,
                bic,
                kullback_leibler,
                ks_stat,
                ks_pval,
            )
        except Exception as e:  # pragma: no cover
            if verbose:
                logger.warning(
                    f"SKIPPED {distribution}: {type(e).__name__} "
                    f"(timeout={timeout}s or fitting failed)"
                )
            return distribution, None

    def fit(
        self,
        progress: bool = False,
        n_jobs: int = -1,
        max_workers: int = -1,
        prefer: str = "processes",
    ) -> None:
        r"""Fit all distributions to the data and compute goodness-of-fit metrics.

        Loops over all distributions in parallel and finds the best parameters to fit
        the data. Populates the following attributes:

            - :attr:`df_errors`: DataFrame with sum of squared errors and information criteria
            - :attr:`fitted_param`: Parameters that best fit the data for each distribution
            - :attr:`fitted_pdf`: PDF values generated with the fitted parameters

        Args:
            progress: If True, display progress bar during fitting.
            n_jobs: Number of jobs for parallel processing (deprecated, use max_workers).
            max_workers: Number of parallel workers (-1 for all CPUs).
            prefer: Joblib parallelization method ('processes' or 'threads').

        Note:
            The fitting uses parallel processing for speed. Distributions that fail
            or timeout are assigned infinite error values.

        """
        n_dists = len(self.distributions)
        with tqdm_joblib(
            desc=f"Fitting {n_dists} distributions",
            total=n_dists,
            disable=not progress,
        ) as progress_bar:
            results = Parallel(n_jobs=max_workers, prefer=prefer)(
                delayed(Fitter._fit_single_distribution)(
                    dist, self._data, self.x, self.y, self.timeout, self.verbose
                )
                for dist in self.distributions
            )

        # Process results and populate dictionaries
        for distribution, values in results:
            if values is not None:
                (
                    param,
                    pdf_fitted,
                    sq_error,
                    aic,
                    bic,
                    kullback_leibler,
                    ks_stat,
                    ks_pval,
                ) = values

                self.fitted_param[distribution] = param
                self.fitted_pdf[distribution] = pdf_fitted
                self._fitted_errors[distribution] = sq_error
                self._aic[distribution] = aic
                self._bic[distribution] = bic
                self._kldiv[distribution] = kullback_leibler
                self._ks_stat[distribution] = ks_stat
                self._ks_pval[distribution] = ks_pval
            else:
                # Assign infinity for failed fits
                self._fitted_errors[distribution] = np.inf
                self._aic[distribution] = np.inf
                self._bic[distribution] = np.inf
                self._kldiv[distribution] = np.inf
                self._ks_stat[distribution] = np.inf
                self._ks_pval[distribution] = 0.0

        # Create results DataFrame
        self.df_errors: pd.DataFrame = pd.DataFrame(
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

    def plot_pdf(
        self,
        names: str | list[str] | None = None,
        Nbest: int = 5,
        lw: float = 2,
        method: str = "sumsquare_error",
    ) -> None:
        """Plot probability density functions of fitted distributions.

        Args:
            names: Distribution name(s) to plot. If None, plots the Nbest distributions.
                   Can be a single string or list of strings.
            Nbest: Number of best-fitting distributions to plot (when names is None).
            lw: Line width for the plots.
            method: Metric to use for ranking distributions ('sumsquare_error', 'aic', 'bic', etc.).

        """
        assert Nbest > 0, "Nbest must be positive"
        Nbest = min(Nbest, len(self.distributions))

        if isinstance(names, list):
            for name in names:
                if name in self.fitted_pdf:
                    plt.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
                else:
                    logger.warning(f"{name} was not fitted successfully")
        elif names:
            if names in self.fitted_pdf:
                plt.plot(self.x, self.fitted_pdf[names], lw=lw, label=names)
            else:
                logger.warning(f"{names} was not fitted successfully")
        else:
            # Get best N distributions by specified method
            try:
                best_names = self.df_errors.sort_values(by=method).index[:Nbest]
            except Exception:
                # Fallback for older pandas versions
                best_names = self.df_errors.sort_values(method).index[:Nbest]

            for name in best_names:
                if name in self.fitted_pdf:
                    plt.plot(self.x, self.fitted_pdf[name], lw=lw, label=name)
                else:  # pragma: no cover
                    logger.warning(f"{name} was not fitted. No parameters available")
        
        plt.grid(True)
        plt.legend()

    def get_best(self, method: str = "sumsquare_error") -> dict[str, dict[str, float]]:
        """Return the best fitted distribution and its parameters.

        Args:
            method: Metric to use for ranking ('sumsquare_error', 'aic', 'bic', etc.).

        Returns:
            Dictionary with distribution name as key and parameter dictionary as value.
            Example: {'gamma': {'a': 2.0, 'loc': 1.5, 'scale': 2.0}}

        """
        # Get best distribution (lowest error/AIC/BIC)
        best_name = self.df_errors.sort_values(method).iloc[0].name
        params = self.fitted_param[best_name]
        distribution = getattr(scipy.stats, best_name)
        
        # Extract parameter names from distribution
        if distribution.shapes:
            param_names = (distribution.shapes + ", loc, scale").split(", ")
        else:
            param_names = ["loc", "scale"]

        # Create parameter dictionary using dict comprehension (faster)
        param_dict = dict(zip(param_names, params))
        return {best_name: param_dict}

    def summary(
        self,
        Nbest: int = 5,
        lw: float = 2,
        plot: bool = True,
        method: str = "sumsquare_error",
        clf: bool = True,
    ) -> pd.DataFrame:
        """Display summary of best fitting distributions.

        Args:
            Nbest: Number of best distributions to include in summary.
            lw: Line width for plots.
            plot: If True, create histogram and PDF overlay plot.
            method: Metric to use for ranking distributions.
            clf: If True, clear figure before plotting.

        Returns:
            DataFrame with fitting results for the Nbest distributions.

        """
        if plot:
            if clf:
                plt.clf()
            self.hist()
            self.plot_pdf(Nbest=Nbest, lw=lw, method=method)
            plt.grid(True)

        Nbest = min(Nbest, len(self.distributions))
        try:
            best_names = self.df_errors.sort_values(by=method).index[:Nbest]
        except Exception:  # pragma: no cover
            # Fallback for older pandas versions
            best_names = self.df_errors.sort_values(method).index[:Nbest]
        return self.df_errors.loc[best_names]

    @staticmethod
    def _with_timeout(
        func: Any,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        """Execute a function with a timeout limit.

        Args:
            func: Function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.
            timeout: Maximum execution time in seconds.

        Returns:
            Result of the function call.

        Raises:
            TimeoutError: If function execution exceeds timeout.

        """
        if kwargs is None:
            kwargs = {}
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
