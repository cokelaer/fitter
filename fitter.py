import scipy.stats
from numpy import array
import pylab


distributions = []
for this in dir(scipy.stats):
    if "fit" in eval("dir(scipy.stats." + this +")"):
        distributions.append(this)



class Fitter(object):

    def __init__(self, data, m=None, M=None, bins=100):
        self.data = array(data)

        self.m = self.data.min()
        self.M = self.data.max()
        if m:
            self.m = m
        if M:
            self.M = M 
        self.distributions = distributions[:]

        self.fitted_param = {}
        self.fitted_pdf = {}
        self.fitted_error = {}

        self.bins = bins
        self.y, self.x, _patches = pylab.hist(self.data, bins=bins, normed=True)
        # y has same length as bins but x has +1 element. Need to pick up
        # average
        self.x = [(this+self.x[i+1])/2. for i,this in enumerate(self.x[0:-1])]

    def fit(self):
        for distribution in self.distributions:
            try:

                # need a subprocess to check time it takes. If too long, skip it 
                dist = eval("scipy.stats." + distribution)
    
                param = dist.fit(self.data)
                pdf_fitted = dist.pdf(self.x, *param) # hoping the order returned by fit is the same as in pdf

                self.fitted_param[distribution] = param[:]
                self.fitted_pdf[distribution] = pdf_fitted

                error = pylab.sqrt(pylab.sum(self.fitted_pdf[distribution] -
                    self.y)**2/self.bins)
                print("Distribution {} with error {}".format(distribution, error))
                self.fitted_error[distribution] = error
            except Exception as err:
                print(err.message)
                print("SKIPPED {}".format(distribution))

    def plot_pdf(self, name):
        pylab.plot(self.x, self.fitted_pdf[name], lw=2)
