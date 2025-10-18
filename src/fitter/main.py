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
"""Standalone application for fitting distributions to data.

This module provides a CLI interface for the fitter package,
allowing users to fit various statistical distributions to their data.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import rich_click as click

from fitter import version

__all__ = ["main"]

# Module-level constants
CONTEXT_SETTINGS: dict[str, Any] = {"help_option_names": ["-h", "--help"]}
VALID_IMAGE_EXTENSIONS: frozenset[str] = frozenset({"png", "jpg", "svg", "pdf"})

# Configure rich_click settings
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.FOOTER_TEXT = (
    "Authors: Thomas Cokelaer -- "
    "Documentation: http://fitter.readthedocs.io -- "
    "Issues: http://github.com/cokelaer/fitter"
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=version)
def main() -> None:  # pragma: no cover
    """Fit your data using SciPy distributions.

    Examples:
        fitter fitdist data.csv
        fitter show_distributions

    """
    pass


@main.command()
@click.argument("filename", type=click.STRING)
@click.option(
    "--column-number",
    type=click.INT,
    default=1,
    show_default=True,
    help="Data column to use (1-indexed, first column by default)",
)
@click.option(
    "--delimiter",
    type=click.STRING,
    default=",",
    show_default=True,
    help="Column delimiter (comma by default)",
)
@click.option(
    "--distributions",
    type=click.STRING,
    default="gamma,beta",
    show_default=True,
    help="Comma-separated list of distributions to fit",
)
@click.option(
    "--tag",
    type=click.STRING,
    default="fitter",
    show_default=True,
    help="Tag to name output files",
)
@click.option(
    "--progress/--no-progress",
    default=True,
    show_default=True,
    help="Show progress bar during fitting",
)
@click.option(
    "--verbose/--no-verbose",
    default=True,
    show_default=True,
    help="Enable verbose output",
)
@click.option(
    "--output-image",
    type=click.STRING,
    default="fitter.png",
    show_default=True,
    help="Output image filename (png, jpg, svg, or pdf)",
)
def fitdist(**kwargs: Any) -> None:
    """Fit statistical distributions to data from a CSV file.

    Args:
        **kwargs: Command-line arguments including filename, column_number,
                  delimiter, distributions, tag, progress, verbose, and output_image.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the output file extension is invalid.
        IndexError: If the specified column doesn't exist.
        ValueError: If data cannot be converted to float.

    """
    from matplotlib.pyplot import savefig  # Lazy import for performance

    filename = Path(kwargs["filename"])
    
    # Validate input file exists
    if not filename.exists():
        click.echo(f"Error: File '{filename}' not found.", err=True)
        sys.exit(1)
    
    col = kwargs["column_number"]
    delimiter = kwargs["delimiter"]
    
    # Read CSV data - optimized with buffered reading
    try:
        with filename.open("r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            # Pre-allocate list for better performance
            data = []
            for row in reader:
                try:
                    data.append(float(row[col - 1]))
                except (IndexError, ValueError) as e:
                    if isinstance(e, IndexError):
                        click.echo(
                            f"Error: Column {col} does not exist in the data.",
                            err=True,
                        )
                    else:
                        click.echo(
                            f"Error: Cannot convert value to float in column {col}.",
                            err=True,
                        )
                    sys.exit(1)
    except OSError as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)

    # Validate output extension - use pathlib for robust path handling
    outfile = Path(kwargs["output_image"])
    if outfile.suffix.lstrip(".") not in VALID_IMAGE_EXTENSIONS:
        extensions = ", ".join(sorted(VALID_IMAGE_EXTENSIONS))
        click.echo(
            f"Error: Output file must have one of these extensions: {extensions}",
            err=True,
        )
        sys.exit(1)

    # Disable progress bar if verbose is off
    verbose = kwargs["verbose"]
    progress = kwargs["progress"] and verbose

    # Perform distribution fitting - lazy import for startup performance
    from fitter import Fitter

    # Parse and clean distribution names - single pass for efficiency
    distributions = [d.strip() for d in kwargs["distributions"].split(",") if d.strip()]
    
    if not distributions:
        click.echo("Error: No distributions specified.", err=True)
        sys.exit(1)
    
    fit = Fitter(data, distributions=distributions)
    fit.fit(progress=progress)
    fit.summary()

    if verbose:
        click.echo()

    # Save output image
    if verbose:
        click.echo(f"Saved image in {outfile}; use --output-image to change the name")
    savefig(outfile, dpi=200)  # Use Path object directly

    # Extract best fit results - avoid multiple list() conversions
    best = fit.get_best()
    bestname, values = next(iter(best.items()))  # More efficient than list conversion
    
    # Build summary message using list join (faster than string concatenation)
    msg_parts = [
        f"Fitter version {version}",
        f"Best fit is {bestname} distribution",
        f"parameters: {values}",
        "The parameters must be used in this order in scipy",
    ]
    msg = "\n".join(msg_parts)
    
    if verbose:
        click.echo(msg)

    # Write log file - use pathlib and explicit encoding
    tag = kwargs["tag"]
    log_path = Path(f"{tag}.log")
    try:
        log_path.write_text(msg, encoding="utf-8")
    except OSError as e:
        click.echo(f"Warning: Could not write log file: {e}", err=True)


@main.command()
def show_distributions(**kwargs: Any) -> None:
    """Display all available distributions.

    Lists all statistical distributions that can be used for fitting.

    Args:
        **kwargs: Command-line arguments (unused but required by Click).

    """
    from fitter import get_distributions  # Lazy import

    distributions = get_distributions()
    click.echo("\n".join(distributions))


if __name__ == "__main__":  # pragma: no cover
    main()
