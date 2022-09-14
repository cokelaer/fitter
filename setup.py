# -*- coding: utf-8 -*-
__revision__ = "$Id: setup.py 3170 2013-01-16 14:57:19Z cokelaer $"
from setuptools import setup, find_packages

_MAJOR               = 1
_MINOR               = 5
_MICRO               = 1
version              = '%d.%d.%d' % (_MAJOR, _MINOR, _MICRO)
release              = '%d.%d' % (_MAJOR, _MINOR)

metainfo = {
    'authors': {'Cokelaer':('Thomas Cokelaer','cokelaer@gmail.com')},
    'version': version,
    'license' : 'GPL',
    'download_url' : 'https://github.com/cokelaer/fitter',
    'url' : "https://github.com/cokelaer/fitter",
    'description':'A tool to fit data to many distributions and best one(s)' ,
    'platforms' : ['Linux', 'Unix', 'MacOsX', 'Windows'],
    'keywords' : ['fit', "distribution", "fitting", "scipy"],
    'classifiers' : [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Topic :: Software Development :: Libraries :: Python Modules'
          ]
    }



setup(
    name             = 'fitter',
    version          = version,
    maintainer       = metainfo['authors']['Cokelaer'][0],
    maintainer_email = metainfo['authors']['Cokelaer'][1],
    author           = metainfo['authors']['Cokelaer'][0],
    author_email     = metainfo['authors']['Cokelaer'][1],
    long_description = open("README.rst").read(),
    keywords         = metainfo['keywords'],
    description = metainfo['description'],
    license          = metainfo['license'],
    platforms        = metainfo['platforms'],
    url              = metainfo['url'],      
    download_url     = metainfo['download_url'],
    classifiers      = metainfo['classifiers'],

    zip_safe=False,
    # package installation
    package_dir = {'':'src'},
    packages = ['fitter'],
    install_requires = open("requirements.txt").read(),
    entry_points = {
        'console_scripts':[
           'fitter=fitter.main:main', 
        ]
    },

)




