import pkg_resources

try:
    version = pkg_resources.require("fitter")[0].version
except Exception:  # pragma: no cover
    version = "unknown"

from .fitter import Fitter, get_distributions, get_common_distributions
from .histfit import HistFit
