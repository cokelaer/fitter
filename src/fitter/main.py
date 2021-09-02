# -*- python -*-
# -*- coding: utf-8 -*-
#
#  This file is part of the fitter software
#
#  Copyright (c) 2014
#
#  File author(s): Thomas Cokelaer <cokelaer@gmail.com>
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  source: https://github.com/cokelaer/fitter
#  Documentation: http://packages.python.org/fitter
#  Package: http://pypi.python.org/fitter
#
##############################################################################
""".. rubric:: Standalone application"""
import os
import glob
import json
import sys
import colorlog
import textwrap
import subprocess
import click
import pathlib

__all__ = ["main"]

from fitter import version

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=version)
def main():  # pragma: no cover
    """This is the main help"""
    pass


@main.command()
@click.argument("filename", type=click.STRING)
@click.option("--column-number", type=click.INT, default=1)
@click.option(
    "--delimiter", type=click.STRING, default=",", help="look at the first column"
)
@click.option(
    "--distributions",
    type=click.STRING,
    default="gamma,beta",
    help="llist of distribution",
)
@click.option(
    "--tag", type=click.STRING, default="fitter", help="tag to name output files"
)
@click.option("--progress/--no-progress", default=True)
@click.option("--verbose/--no-verbose", default=True)
def fitdist(**kwargs):
    """"""
    import csv

    col = kwargs["column_number"]
    with open(kwargs["filename"], "r") as csvfile:
        data = csv.reader(csvfile, delimiter=kwargs["delimiter"])
        data = [float(x[col - 1]) for x in data]

    from fitter import Fitter

    distributions = kwargs["distributions"].split(",")
    distributions = [x.strip() for x in distributions]
    fit = Fitter(data, distributions=distributions)

    if kwargs["verbose"] is False:
        kwargs["progress"] = False
    fit.fit(progress=kwargs["progress"])
    fit.summary()
    if kwargs["verbose"]:
        print()
    from pylab import savefig

    if kwargs["verbose"]:
        print("Saved image in fitter.png; use --output-image to change the name")
    tag = kwargs["tag"]
    savefig("{}.png".format(tag))

    best = fit.get_best()
    bestname = list(best.keys())[0]
    values = list(best.values())[0]
    msg = f"Fitter version {version}\nBest fit is {bestname} distribution\nparameters: "
    msg += f"{values}\n The parameters have to be used in that order in scipy"
    if kwargs["verbose"]:
        print(msg)
    with open("{}.log".format(tag), "w") as fout:
        fout.write(msg)


if __name__ == "__main__":  # pragma: no cover
    main()
