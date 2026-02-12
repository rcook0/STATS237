from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def get_package_version(default: str = "1.0.0") -> str:
    """Return the installed package version.

    When running from a source tree without installation, falls back to `default`.
    """
    try:
        return version("stats237-quantlib")
    except PackageNotFoundError:
        return default
