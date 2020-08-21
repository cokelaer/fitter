Change Log
##########

**1.2.2**

* remove vervose arguments in Fitter class. Using the logging module instead
* the Fitte.fit has now a progress bar
* add a standalone application called ... fitter (see the doc)

**1.2.1**

* adding new class called histfit (see documentation)

**1.2**

* Fixed the version. Previous version switched from 1.0.9 to 1.1.11. To start a
  fresh version, we increase to 1.2.0
* Merged pull request required by bioconda
* Merged pull request related to implementation of AIC/BIC/KL criteria
  (https://github.com/cokelaer/fitter/pull/19). 
  This also fixes https://github.com/cokelaer/fitter/issues/9
* Implement two functions to get all distributions, or a list of common
  distributions to help users decreading computational time 
  (https://github.com/cokelaer/fitter/issues/20). Also added a FAQS section.
* travis tested Python 3.6 and 3.7 (not 3.5 anymore)

**1.1**

* Fixed deprecated warning
* Fitter is now in readthedocs at fitter.readthedocs.io

**1.0.9**

* https://github.com/cokelaer/fitter/pull/8 and 11
* PR https://github.com/cokelaer/fitter/pull/8

**1.0.6**


* summary() now returns the dataframe (instead of printing it)

**1.0.5**

* https://github.com/cokelaer/fitter/issues

**1.0.2**


* add manifest to fix missing source in the pypi repository.
