"""NSRL Lookup Server."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "1.0.0"
