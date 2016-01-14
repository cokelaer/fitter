import pkg_resources
try:
    version = pkg_resources.require("pypiview")[0].version
except Exception:
    version = "unknown"

from .fitter import Fitter
