from fitter import Fitter, get_distributions, get_common_distributions


def test_dist():
    assert 'gamma' in get_common_distributions()
    assert len(get_distributions())> 40



def test_fitter():
    f = Fitter([1,1,1,2,2,2,2,2,3,3,3,3], distributions=['gamma'], xmin=0, xmax=4)
    try:
        f.plot_pdf()
    except:
        pass
    f.fit()
    f.summary()
    assert f.xmin == 0
    assert f.xmax == 4

    # reset the range:
    f.xmin = None
    f.xmax = None
    assert f.xmin == 1
    assert f.xmax == 3


    f = Fitter([1,1,1,2,2,2,2,2,3,3,3,3], distributions=['gamma'])
    f.fit()
    f.summary()
    assert f.xmin == 1
    assert f.xmax == 3


def test_gamma():
    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=10000)


    f = Fitter(data, bins=100)
    f.xmin = -10 #should have no effect
    f.xmax = 1000000 # no effet
    f.xmin=0.1
    f.xmax=10
    f.distributions = ['gamma', "alpha"]
    f.fit()
    df = f.summary()
    assert len(df)

    f.plot_pdf(names=["gamma"])
    f.plot_pdf(names="gamma")

    res = f.get_best()
    assert "gamma" in res.keys()


def test_others():
    from scipy import stats
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=1000)
    f = Fitter(data, bins=100, distributions="common")
    f.fit()
    assert f.df_errors.loc["gamma"].loc['aic'] > 100

    f = Fitter(data, bins=100, distributions="gamma")
    f.fit()
    assert f.df_errors.loc["gamma"].loc['aic'] > 100










