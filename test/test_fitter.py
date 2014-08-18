from fitter import Fitter



def test_fitter():

    f = fitter([1,1,1,2,2,2,2,2,3,3,3,3], distributions=['gamma'])
    f.fit()
    f.summary()
