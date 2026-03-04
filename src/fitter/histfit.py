"""Histogram fitting module for Gaussian distributions.

This module provides functionality to fit Gaussian distributions to histogram data,
with support for error estimation through Monte Carlo sampling.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import scipy.optimize  # BUGFIX: Missing import caused runtime error
import scipy.stats
from matplotlib import pyplot as plt

__all__ = ["HistFit"]


class HistFit:
    """Fit and plot Gaussian distributions to histogram data.

    This class fits a Gaussian (normal) distribution to histogram data using
    least squares optimization with optional Monte Carlo error estimation.

    The input can be either:
    - Raw data: Histogram is computed automatically
    - Pre-computed histogram: X (bin centers) and Y (densities) arrays

    For better parameter estimation, the fit can be repeated with added noise
    (controlled by error_rate) to estimate uncertainty in mu, sigma, and amplitude.

    Examples:
        >>> from fitter import HistFit
        >>> import scipy.stats
        >>> data = [scipy.stats.norm.rvs(2, 3.4) for _ in range(10000)]
        >>> hf = HistFit(data, bins=30)
        >>> hf.fit(error_rate=0.03, Nfit=20)
        >>> print(hf.mu, hf.sigma, hf.amplitude)

        Using pre-computed histogram:
        >>> Y, X, _ = plt.hist(data, bins=30, density=True)
        >>> hf = HistFit(X=X, Y=Y)
        >>> hf.fit(error_rate=0.03, Nfit=20)

    Attributes:
        mu (float): Mean of the fitted Gaussian distribution.
        sigma (float): Standard deviation of the fitted distribution.
        amplitude (float): Amplitude scaling factor.
        X (np.ndarray): Bin centers of the histogram.
        Y (np.ndarray): Probability density values.

    Warning:
        Currently handles only Gaussian distributions. API may change in future versions.

    """

    def __init__(
        self,
        data: list[float] | np.ndarray | None = None,
        X: np.ndarray | None = None,
        Y: np.ndarray | None = None,
        bins: int | None = None,
    ) -> None:
        """Initialize HistFit with either raw data or pre-computed histogram.

        Args:
            data: Raw data array to compute histogram from.
            X: Pre-computed histogram bin edges or centers.
            Y: Pre-computed probability density values.
            bins: Number of bins if data is provided (passed to histogram function).

        Raises:
            ValueError: If neither data nor (X, Y) are provided.

        """
        self.data = np.asarray(data) if data is not None else None
        
        if data is not None:
            # Compute histogram with density normalization
            Y, X = np.histogram(self.data, bins=bins, density=True)
            self.N: int = len(X) - 1
            # Vectorized bin center calculation (faster than list comprehension)
            self.X: np.ndarray = (X[:-1] + X[1:]) / 2
            self.Y: np.ndarray = Y
            self.A: float = 1.0
            # Use numpy functions for vectorized operations (much faster)
            self.guess_std: float = float(np.std(self.data))
            self.guess_mean: float = float(np.mean(self.data))
            self.guess_amp: float = 1.0
        else:
            # Use pre-computed histogram
            self.X = np.asarray(X)
            self.Y = np.asarray(Y)
            # Normalize Y to sum to 1 (probability density)
            y_sum = np.sum(self.Y)
            if y_sum > 0:
                self.Y = self.Y / y_sum
            
            # Handle case where X has N+1 values (bin edges) and Y has N values
            if len(self.X) == len(self.Y) + 1:
                # Vectorized bin center calculation (much faster)
                self.X = (self.X[:-1] + self.X[1:]) / 2

            self.N = len(self.X)
            # Use median as initial guess for mean (more robust)
            self.guess_mean = float(np.median(self.X))
            # BUGFIX: Correct standard deviation estimation
            # Original formula was incorrect: divided by sqrt(2*pi) which makes no sense
            # Proper std calculation from weighted histogram data:
            self.guess_std = float(np.sqrt(np.average((self.X - np.average(self.X, weights=self.Y))**2, weights=self.Y)))
            self.guess_amp = 1.0

        self.func = self._func_normal

    def fit(
        self,
        error_rate: float = 0.05,
        semilogy: bool = False,
        Nfit: int = 100,
        error_kwargs: dict[str, Any] | None = None,
        fit_kwargs: dict[str, Any] | None = None,
    ) -> tuple[float, float, float]:
        """Fit Gaussian distribution to histogram data with error estimation.

        Performs multiple fits with added noise to estimate parameter uncertainty.
        Creates two figures: one showing individual fits, another showing uncertainty bands.

        Args:
            error_rate: Relative error to add as Gaussian noise (e.g., 0.05 = 5%).
            semilogy: If True, use logarithmic y-axis for the plot.
            Nfit: Number of Monte Carlo iterations for error estimation.
            error_kwargs: Plotting kwargs for individual noisy fits (default: thin black transparent lines).
            fit_kwargs: Plotting kwargs for final averaged fit (default: thick red line).

        Returns:
            Tuple of (mu, sigma, amplitude) from the averaged fit.

        """
        # Handle mutable default arguments (PEP best practice)
        if error_kwargs is None:
            error_kwargs = {"lw": 1, "color": "black", "alpha": 0.2}
        if fit_kwargs is None:
            fit_kwargs = {"lw": 2, "color": "red"}
        # Pre-allocate arrays for better performance (avoid dynamic resizing)
        self.mus: np.ndarray = np.zeros(Nfit)
        self.sigmas: np.ndarray = np.zeros(Nfit)
        self.amplitudes: np.ndarray = np.zeros(Nfit)
        self.fits: np.ndarray = np.zeros((Nfit, self.N))

        plt.figure(1)
        plt.clf()
        # Use width based on actual bin spacing for proper visualization
        bin_width = np.diff(self.X).mean() if len(self.X) > 1 else 0.85
        plt.bar(self.X, self.Y, width=bin_width * 0.85, ec="k")

        for i in range(Nfit):
            # Add Gaussian noise for error estimation (vectorized for speed)
            self.E: np.ndarray = np.random.normal(0, error_rate, self.N)
            
            # Perform least squares optimization
            self.result = scipy.optimize.least_squares(
                self.func,
                (self.guess_mean, self.guess_std, self.guess_amp),
            )

            mu, sigma, amplitude = self.result["x"]
            # Cache the PDF calculation to avoid computing twice
            fitted_curve = amplitude * scipy.stats.norm.pdf(self.X, mu, sigma)
            plt.plot(self.X, fitted_curve, **error_kwargs)
            
            # Store results in pre-allocated arrays (much faster than append)
            self.sigmas[i] = sigma
            self.amplitudes[i] = amplitude
            self.mus[i] = mu
            self.fits[i] = fitted_curve

        # Compute mean parameters from all fits (numpy vectorized operations)
        self.sigma: float = float(np.mean(self.sigmas))
        self.amplitude: float = float(np.mean(self.amplitudes))
        self.mu: float = float(np.mean(self.mus))

        # Plot final averaged fit
        final_fit = self.amplitude * scipy.stats.norm.pdf(self.X, self.mu, self.sigma)
        plt.plot(self.X, final_fit, **fit_kwargs)
        if semilogy:
            plt.yscale("log")
        plt.grid(True)

        # Create uncertainty visualization figure
        plt.figure(2)
        plt.clf()
        
        # Compute mean and std across all Monte Carlo fits (vectorized)
        M = np.mean(self.fits, axis=0)
        S = np.std(self.fits, axis=0)
        
        # Plot confidence bands: 3σ (~99.7%), 2σ (~95%), 1σ (~68%)
        plt.fill_between(self.X, M - 3 * S, M + 3 * S, color="gray", alpha=0.3, label="3σ")
        plt.fill_between(self.X, M - 2 * S, M + 2 * S, color="gray", alpha=0.4, label="2σ")
        plt.fill_between(self.X, M - S, M + S, color="gray", alpha=0.5, label="1σ")
        
        # Plot final fit line (use cached calculation)
        plt.plot(self.X, final_fit, **fit_kwargs, label="Mean fit")
        plt.grid(True)
        plt.legend()

        return self.mu, self.sigma, self.amplitude

    def _func_normal(self, param: tuple[float, float, float]) -> np.ndarray:
        """Objective function for least squares fitting of Gaussian distribution.

        Computes the squared residuals between the fitted Gaussian and the observed
        histogram data (with added noise for error estimation).

        Args:
            param: Tuple of (mu, sigma, amplitude) parameters to optimize.

        Returns:
            Array of squared residuals for least squares optimization.

        Note:
            For a normalized Gaussian, amplitude would be 1/(sqrt(2π)·σ),
            but here we allow it to be a free parameter for flexibility.

        """
        mu, sigma, A = param
        # Vectorized computation (much faster than Python sum/loop)
        # Returns residual vector for scipy.optimize.least_squares
        fitted = A * scipy.stats.norm.pdf(self.X, mu, sigma)
        observed = self.Y + self.E
        return fitted - observed
