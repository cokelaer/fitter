from fitter import Fitter



def test_fitter():
    f = Fitter([1,1,1,2,2,2,2,2,3,3,3,3], distributions=['gamma'], xmin=0, xmax=4)
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
    data = stats.gamma.rvs(2, loc=1.5, scale=2, size=100000)


    f = Fitter(data, bins=100)
    f.xmin = -10 #should have no effect
    f.xmax = 1000000 # no effet
    f.xmin=0.1
    f.xmax=10
    f.distributions = f.distributions[:3:]
    f.fit()
    df = f.summary()
    assert len(df)

    f.plot_pdf(names=['anglit', 'alpha'])
