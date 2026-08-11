"""Parsing and validation of the a_maze_ing configuration file.

The file holds one ``KEY=VALUE`` pair per line. Blank lines and lines whose
first non-blank character is ``#`` are ignored. Keys are case-insensitive
and surrounding whitespace is stripped from both sides of the ``=``.

Parsing is all-or-nothing: :func:`load_config` either returns a fully
validated :class:`MazeConfig` or raises :class:`~errors.ConfigError`. It
never returns a half-checked object, so the rest of the program can trust
the values it receives without re-testing them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from errors import ConfigError

REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}
)

MIN_SIDE: Final[int] = 2
MAX_SIDE: Final[int] = 500

PATTERN_MIN_WIDTH: Final[int] = 9
PATTERN_MIN_HEIGHT: Final[int] = 7

TRUE_WORDS: Final[frozenset[str]] = frozenset({"true", "yes", "on", "1"})
FALSE_WORDS: Final[frozenset[str]] = frozenset({"false", "no", "off", "0"})


@dataclass(frozen=True)
class MazeConfig:
    """A validated maze configuration.

    Coordinates are ``(x, y)`` pairs where ``x`` is the column index and
    ``y`` the row index. This matches the configuration file, the output
    file footer and :class:`mazegen.MazeGenerator`, so no conversion is
    needed anywhere in this program.

    Attributes:
        width: Number of cells per row.
        height: Number of rows.
        entry: Entry cell as ``(x, y)``.
        exit: Exit cell as ``(x, y)``.
        output_file: Path the maze is written to.
        perfect: True for a single-path maze, False for a Pac-Man board.
        seed: Seed for reproducible generation, or None for a random maze.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None

    @property
    def fits_pattern(self) -> bool:
        """Whether the grid is large enough to hold the "42" pattern."""
        return (
            self.width >= PATTERN_MIN_WIDTH
            and self.height >= PATTERN_MIN_HEIGHT
        )


def _read_pairs(path: str) -> dict[str, str]:
    """Read *path* and return its ``KEY=VALUE`` pairs.

    Args:
        path: Path to the configuration file.

    Returns:
        A mapping of upper-cased keys to their raw string values.

    Raises:
        ConfigError: The file cannot be read, or a line is malformed.
    """
    pairs: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as stream:
            for number, raw in enumerate(stream, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                key, separator, value = line.partition("=")
                if not separator:
                    raise ConfigError(
                        f"{path}, line {number}: missing '=' in "
                        f"{line!r} (expected KEY=VALUE)."
                    )
                key = key.strip().upper()
                if not key:
                    raise ConfigError(
                        f"{path}, line {number}: the key is empty."
                    )
                if key in pairs:
                    raise ConfigError(
                        f"{path}, line {number}: {key} is defined twice."
                    )
                pairs[key] = value.strip()
    except FileNotFoundError:
        raise ConfigError(f"configuration file not found: {path}") from None
    except IsADirectoryError:
        raise ConfigError(f"{path} is a directory, not a file.") from None
    except PermissionError:
        raise ConfigError(f"no permission to read {path}.") from None
    except UnicodeDecodeError:
        raise ConfigError(
            f"{path} is not readable as UTF-8 text."
        ) from None
    except OSError as error:
        raise ConfigError(f"cannot read {path}: {error}") from None
    return pairs


def _require(pairs: dict[str, str], key: str) -> str:
    """Return ``pairs[key]``, or raise if it is absent or blank."""
    value = pairs.get(key)
    if value is None:
        raise ConfigError(f"missing mandatory key: {key}")
    if not value:
        raise ConfigError(f"{key} has no value.")
    return value


def _to_int(key: str, raw: str) -> int:
    """Convert *raw* to an int, naming *key* in the error message."""
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(
            f"{key} must be a whole number (got {raw!r})."
        ) from None


def _to_bool(key: str, raw: str) -> bool:
    """Convert *raw* to a bool, naming *key* in the error message."""
    word = raw.lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ConfigError(
        f"{key} must be True or False (got {raw!r})."
    )


def _to_point(key: str, raw: str) -> tuple[int, int]:
    """Convert an ``x,y`` string to a coordinate pair."""
    parts = raw.split(",")
    if len(parts) != 2:
        raise ConfigError(
            f"{key} must be two numbers separated by a comma, "
            f"as in 0,0 (got {raw!r})."
        )
    x = _to_int(f"{key} x-coordinate", parts[0].strip())
    y = _to_int(f"{key} y-coordinate", parts[1].strip())
    return x, y


def _check_side(name: str, value: int) -> None:
    """Raise if a grid dimension is outside the supported range."""
    if value < MIN_SIDE:
        raise ConfigError(
            f"{name} must be at least {MIN_SIDE} (got {value})."
        )
    if value > MAX_SIDE:
        raise ConfigError(
            f"{name} must be at most {MAX_SIDE} (got {value})."
        )


def _check_inside(
    name: str, point: tuple[int, int], width: int, height: int
) -> None:
    """Raise if *point* falls outside a ``width`` x ``height`` grid."""
    x, y = point
    if not 0 <= x < width:
        raise ConfigError(
            f"{name} x-coordinate {x} is outside the maze "
            f"(valid range 0..{width - 1})."
        )
    if not 0 <= y < height:
        raise ConfigError(
            f"{name} y-coordinate {y} is outside the maze "
            f"(valid range 0..{height - 1})."
        )


def load_config(path: str) -> MazeConfig:
    """Read, parse and validate the configuration file at *path*.

    Args:
        path: Path to the configuration file.

    Returns:
        A fully validated configuration.

    Raises:
        ConfigError: The file is unreadable, a mandatory key is missing,
            a value has the wrong type, or the values describe an
            impossible maze.
    """
    pairs = _read_pairs(path)

    missing = sorted(REQUIRED_KEYS - pairs.keys())
    if missing:
        raise ConfigError(
            f"missing mandatory key(s): {', '.join(missing)}"
        )

    width = _to_int("WIDTH", _require(pairs, "WIDTH"))
    height = _to_int("HEIGHT", _require(pairs, "HEIGHT"))
    _check_side("WIDTH", width)
    _check_side("HEIGHT", height)

    entry = _to_point("ENTRY", _require(pairs, "ENTRY"))
    exit_ = _to_point("EXIT", _require(pairs, "EXIT"))
    _check_inside("ENTRY", entry, width, height)
    _check_inside("EXIT", exit_, width, height)
    if entry == exit_:
        raise ConfigError(
            f"ENTRY and EXIT are the same cell {entry}; they must differ."
        )

    seed_raw = pairs.get("SEED", "").strip()
    seed = _to_int("SEED", seed_raw) if seed_raw else None
    output_file = _require(pairs, "OUTPUT_FILE")
    if "\x00" in output_file:
        raise ConfigError("OUTPUT_FILE cannot contain a NUL byte.")

    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=output_file,
        perfect=_to_bool("PERFECT", _require(pairs, "PERFECT")),
        seed=seed,
    )
