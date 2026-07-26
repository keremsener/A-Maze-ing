"""Exception hierarchy for a_maze_ing.

Every error this project raises on purpose inherits from
:class:`AMazeIngError`. The top-level entry point catches that one base
class, prints a single readable message and exits with a non-zero status.
No other layer is allowed to swallow an error: a function that detects a
problem raises, and lets the caller decide.
"""

from __future__ import annotations


class AMazeIngError(Exception):
    """Base class for every expected failure in this project."""


class ConfigError(AMazeIngError):
    """The configuration file is missing, unreadable or invalid."""


class OutputError(AMazeIngError):
    """The maze could not be written to the output file."""


class RenderError(AMazeIngError):
    """The graphical display could not be started or drawn."""
