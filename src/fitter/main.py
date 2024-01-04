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
import csv
import glob
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import rich_click as click

__all__ = ["main"]

from fitter import version

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.FOOTER_TEXT = "Authors: Thomas Cokelaer -- Documentation: http://fitter.readthedocs.io -- Issues: http://github.com/cokelaer/fitter"


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=version)
def main():  # pragma: no cover
    """fitter can fit your data using Scipy distributions

    Example:

        fitter fitdist data.csv

    """
    pass


@main.command()
@click.argument("filename", type=click.STRING)
@click.option(
    "--column-number", type=click.INT, default=1, show_default=True, help="data column to use (first column by default)"
)
@click.option(
    "--delimiter", type=click.STRING, default=",", show_default=True, help="column delimiter (comma by default)"
)
@click.option(
    "--distributions",
    type=click.STRING,
    default="gamma,beta",
    show_default=True,
    help="list of distribution",
)
@click.option("--tag", type=click.STRING, default="fitter", help="tag to name output files")
@click.option("--progress/--no-progress", default=True, show_default=True)
@click.option("--verbose/--no-verbose", default=True, show_default=True)
@click.option("--output-image", type=click.STRING, default="fitter.png", show_default=True)
def fitdist(**kwargs):
    """fit distribution"""
    from pylab import savefig

    col = kwargs["column_number"]
    with open(kwargs["filename"], "r") as csvfile:
        data = csv.reader(csvfile, delimiter=kwargs["delimiter"])
        data = [float(x[col - 1]) for x in data]

    # check output extension
    outfile = kwargs["output_image"]
    if Path(outfile).name.split(".")[-1] not in ["png", "jpg", "svg", "pdf"]:
        click.echo("output file must have one of the following extension: png, svg, pdf, jpg", err=True)
        sys.exit(1)

    if kwargs["verbose"] is False:
        kwargs["progress"] = False

    # actual computation
    from fitter import Fitter

    distributions = kwargs["distributions"].split(",")
    distributions = [x.strip() for x in distributions]
    fit = Fitter(data, distributions=distributions)
    fit.fit(progress=kwargs["progress"])
    fit.summary()

    if kwargs["verbose"]:
        click.echo()

    # save image
    if kwargs["verbose"]:
        click.echo("Saved image in fitter.png; use --output-image to change the name")
    savefig(f"{outfile}", dpi=200)

    # additional info in the log file
    best = fit.get_best()
    bestname = list(best.keys())[0]
    values = list(best.values())[0]
    msg = f"Fitter version {version}\nBest fit is {bestname} distribution\nparameters: "
    msg += f"{values}\n The parameters have to be used in that order in scipy"
    if kwargs["verbose"]:
        click.echo(msg)

    tag = kwargs["tag"]
    with open(f"{tag}.log", "w") as fout:
        fout.write(msg)


@main.command()
def show_distributions(**kwargs):
    from fitter import get_distributions

    click.echo("\n".join(get_distributions()))


if __name__ == "__main__":  # pragma: no cover
    main()
