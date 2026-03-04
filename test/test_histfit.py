def test1():
    import scipy.stats

    from fitter import HistFit

    data = [scipy.stats.norm.rvs(2, 3.4) for x in range(10000)]
    hf = HistFit(data, bins=30)
    hf.fit(error_rate=0.03, Nfit=20)
    print(hf.mu, hf.sigma, hf.amplitude)


def test2():
    import scipy.stats
    from pylab import hist

    from fitter import HistFit

    data = [scipy.stats.norm.rvs(2, 3.4) for x in range(10000)]
    Y, X, _ = hist(data, bins=30)
    hf = HistFit(X=X, Y=Y)
    hf.fit(error_rate=0.03, Nfit=20, semilogy=True)
    print(hf.mu, hf.sigma, hf.amplitude)
