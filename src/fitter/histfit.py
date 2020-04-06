import scipy.stats
import pylab
from pylab import mean, sqrt, std


__all__ = ['HistFit']

class HistFit():
    """Plot the histogram of the data (barplot) and the fitted histogram.

    The input data can be a series. In this case, we compute the histogram. 
    Then, we fit a curve on top on the histogram that best fit the histogram.

    If you already have the histogram, you can provide the arguments. 
    In this case, X should be evenly spaced

    

    If you have some data, histogram is computed, then we add some noise during
    the fitting process and repeat the process Nfit=20 times. This gives us a
    better estimate of the underlying mu and sigma parameters of the distribution.

    .. plot::

        from fitter import HistFit
        import scipy.stats
        data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
        hf = HistFit(data, bins=30)
        hf.fit(error_rate=0.03, Nfit=20 )
        print(hf.mu, hf.sigma, hf.amplitude)

    You may already have your probability density function with the X and Y
    series. If so, just provide them; Note that the output of the hist function
    returns an X with N+1 values while Y has only N values. We take care of that. 

    .. plot::

        from fitter import HistFit
        from pylab import hist
        import scipy.stats
        data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
        Y, X, _ = hist(data, bins=30)
        hf = HistFit(X=X, Y=Y)
        hf.fit(error_rate=0.03, Nfit=20)
        print(hf.mu, hf.sigma, hf.amplitude)


    .. warning:: This is a draft class. It currently handles only gaussian
        distribution. The API is probably going to change in the close future.

    """
    def __init__(self, data=None, X=None, Y=None, bins=None):
        """.. rubric:: **Constructor**

        One should provide either the parameter **data** alone, or the X and Y
        parameters, which are the histogram of some data sample.

        :param data: random data
        :param X: evenly spaced X data
        :param Y: probability density of the data
        :param bins: if data is providede, we will compute the probability using
            hist function and bins may be provided. 

        """

        self.data = data
        if data:
            Y, X, _ = pylab.hist(self.data, bins=bins, density=True)
            self.N = len(X) - 1
            self.X = [(X[i]+X[i+1])/2 for i in range(self.N)]
            self.Y = Y
            self.A = 1
            self.guess_std = pylab.std(self.data)
            self.guess_mean = pylab.mean(self.data)
            self.guess_amp = 1
        else:
            self.X = X
            self.Y = Y
            self.Y = self.Y / sum(self.Y)
            if len(self.X) == len(self.Y) + 1 :
                self.X = [(X[i]+X[i+1])/2 for i in range(len(X)-1)]

            self.N = len(self.X)
            self.guess_mean = self.X[int(self.N/2)]
            self.guess_std = sqrt(sum((self.X - mean(self.X))**2)/self.N)/(sqrt(2*3.14))
            self.guess_amp = 1.

        self.func = self._func_normal

    def fit(self, error_rate=0.05, semilogy=False, Nfit=100,
            error_kwargs={"lw":1, "color":"black", "alpha":0.2},
            fit_kwargs={"lw":2, "color":"red"}):
        self.mus = []
        self.sigmas = []
        self.amplitudes = []
        self.fits = []

        pylab.figure(1)
        pylab.clf()
        pylab.bar(self.X, self.Y, width=0.85, ec="k")

        for x in range(Nfit):
            # 10% error on the data to add errors 
            self.E = [scipy.stats.norm.rvs(0, error_rate) for y in self.Y]
            #[scipy.stats.norm.rvs(0, self.std_data * error_rate) for x in range(self.N)]
            self.result = scipy.optimize.least_squares(self.func, 
                (self.guess_mean, self.guess_std, self.guess_amp))

            mu, sigma, amplitude = self.result['x']
            pylab.plot(self.X, amplitude * scipy.stats.norm.pdf(self.X, mu,sigma),
                **error_kwargs)
            self.sigmas.append(sigma)
            self.amplitudes.append(amplitude)
            self.mus.append(mu)


            self.fits.append(amplitude * scipy.stats.norm.pdf(self.X, mu,sigma))

        self.sigma = mean(self.sigmas)
        self.amplitude = mean(self.amplitudes)
        self.mu = mean(self.mus)


        pylab.plot(self.X, self.amplitude * scipy.stats.norm.pdf(self.X, self.mu, self.sigma), 
                   **fit_kwargs)
        if semilogy:
            pylab.semilogy() 
        pylab.grid()

        pylab.figure(2)
        pylab.clf()
        #pylab.bar(self.X, self.Y, width=0.85, ec="k", alpha=0.5)
        M = mean(self.fits, axis=0)
        S = pylab.std(self.fits, axis=0)
        pylab.fill_between(self.X, M-3*S, M+3*S, color="gray", alpha=0.5)
        pylab.fill_between(self.X, M-2*S, M+2*S, color="gray", alpha=0.5)
        pylab.fill_between(self.X, M-S, M+S, color="gray", alpha=0.5)
        #pylab.plot(self.X, M-S, color="k")
        #pylab.plot(self.X, M+S, color="k")
        pylab.plot(self.X, self.amplitude * scipy.stats.norm.pdf(self.X, self.mu, self.sigma), 
                   **fit_kwargs)
        pylab.grid()

        return self.mu, self.sigma, self.amplitude


    def _func_normal(self, param):
        # amplitude is supposed to be 1./(np.sqrt(2*np.pi)*sigma)* if normalised
        mu, sigma, A = param
        return sum( (A*scipy.stats.norm.pdf(self.X,mu, sigma) - (self.Y+self.E))**2)

