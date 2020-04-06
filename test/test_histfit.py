from fitter import Fitter, get_distributions, get_common_distributions



def test1():
    from fitter import HistFit
    import scipy.stats
    data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
    hf = HistFit(data, bins=30)
    hf.fit(error_rate=0.03, Nfit=20 )
    print(hf.mu, hf.sigma, hf.amplitude)

    
def test2():
    from fitter import HistFit
    from pylab import hist
    import scipy.stats
    data = [scipy.stats.norm.rvs(2,3.4) for x in  range(10000)]
    Y, X, _ = hist(data, bins=30)
    hf = HistFit(X=X, Y=Y)
    hf.fit(error_rate=0.03, Nfit=20)
    print(hf.mu, hf.sigma, hf.amplitude)












