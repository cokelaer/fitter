from importlib import metadata


def get_package_version(package_name):
    try:
        version = metadata.version(package_name)
        return version
    except metadata.PackageNotFoundError:  # pragma: no cover
        return f"{package_name} not found"


version = get_package_version("fitter")


from .fitter import Fitter, get_common_distributions, get_distributions
from .histfit import HistFit
