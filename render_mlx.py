"""Graphical display of a maze with the MiniLibX library.

The maze is painted into a single MiniLibX image and pushed to the window
in one call, which is far cheaper than one ``mlx_pixel_put`` per pixel.

The image is built the way a maze is carved: the whole surface starts as
wall, then every cell interior is cleared, then every open wall is cleared
to join two neighbouring interiors. Because the generator keeps both sides
of a shared wall in agreement, clearing from one side is enough.

Three traits of MiniLibX 2.2 (mlx_CLXV) shape the code below, and all
three differ from the older X11 MiniLibX:

* The fourth byte of a pixel is a real alpha channel and it means
  opacity, not transparency. The GPU blends every image with
  ``SRC_ALPHA`` over a window cleared to opaque black, so a pixel
  written with alpha 0 is simply never drawn. Every pixel written here
  is therefore fully opaque.
* ``mlx_get_data_addr`` reports the image *format*, not the endianness:
  0 means the bytes run B, G, R, A and 1 means A, R, G, B.
* Image memory belongs to the GPU while a frame is in flight, so it has
  to be reclaimed with ``mlx_sync`` before being written again.

Two further limits are not documented in ``mlx.h`` but are visible in the
MiniLibX sources, and both show up as a black or flickering window on
some machines only:

* A frame holds at most ``VK_NB_DRAW`` (64) draw calls, and
  ``mlx_string_put`` spends one per character. Going over that forces a
  half-drawn frame on screen, and if the swapchain is unhealthy the
  draw list index is never reset, which overruns it. The status bar is
  therefore kept short on purpose.
* MiniLibX never rebuilds its swapchain, and treats ``VK_SUBOPTIMAL_KHR``
  as a fatal error. Once a window manager resizes the window, every
  later frame is dropped. The window is sized to the real screen so no
  window manager ever needs to resize it.
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Final

from errors import AMazeIngError, RenderError
from view import Scene, Theme, THEMES

MAX_WINDOW_WIDTH: Final[int] = 1200
MAX_WINDOW_HEIGHT: Final[int] = 780
MIN_CELL: Final[int] = 4
MAX_CELL: Final[int] = 44

# Room left for the title bar, panels and docks, so that the window
# manager never has to shrink the window. See window_budget().
SCREEN_MARGIN_X: Final[int] = 80
SCREEN_MARGIN_Y: Final[int] = 140

# MiniLibX 2.2 queues at most VK_NB_DRAW (64) draw calls per frame, and
# mlx_string_put costs one per character. Going over that forces a
# half-finished frame on screen, so the status bar is kept short.
MAX_DRAWS_PER_FRAME: Final[int] = 64

# Height, in pixels, of one line of the built-in MiniLibX font.
FONT_HEIGHT: Final[int] = 20
STATUS_LINES: Final[int] = 2
STATUS_PADDING: Final[int] = 5
STATUS_HEIGHT: Final[int] = (
    STATUS_LINES * FONT_HEIGHT + (STATUS_LINES + 1) * STATUS_PADDING
)
STATUS_COLOUR: Final[int] = 0xFFFFFF

# Alpha value of a fully visible pixel, and the two image layouts that
# mlx_get_data_addr can report.
OPAQUE: Final[int] = 0xFF
FORMAT_BGRA: Final[int] = 0
FORMAT_ARGB: Final[int] = 1

# mlx_sync command that waits until an image can be written again.
SYNC_IMAGE_WRITABLE: Final[int] = 1

KEY_ESC: Final[int] = 65307
KEY_Q: Final[int] = 113
KEY_ONE: Final[int] = 49
KEY_TWO: Final[int] = 50
KEY_THREE: Final[int] = 51
KEY_FOUR: Final[int] = 52
EVENT_DESTROY: Final[int] = 17
EVENT_CLOSE: Final[int] = 33

NORTH: Final[int] = 1
EAST: Final[int] = 2
SOUTH: Final[int] = 4
WEST: Final[int] = 8


def cell_size(
    width: int,
    height: int,
    budget_width: int = MAX_WINDOW_WIDTH,
    budget_height: int = MAX_WINDOW_HEIGHT,
) -> tuple[int, int]:
    """Return the pixel size of one cell and of its wall, for a grid.

    Args:
        width: Number of cells per row.
        height: Number of rows.
        budget_width: Largest window width the display can take.
        budget_height: Largest window height the display can take.

    Returns:
        A ``(cell, wall)`` pair in pixels, as large as the budget allows.
        The pair may still be too large when the grid has more cells than
        the screen has pixels; :func:`window_size` reports the result and
        the caller decides.
    """
    usable = max(MIN_CELL, budget_height - STATUS_HEIGHT)
    cell = min(
        MAX_CELL,
        max(MIN_CELL, budget_width // max(width, 1)),
        max(MIN_CELL, usable // max(height, 1)),
    )
    # A maze is one wall wider and taller than its cells, so the first
    # estimate can overshoot by up to one wall. Shrink until it fits.
    while cell > MIN_CELL:
        window = window_size(width, height, cell)
        if window[0] <= budget_width and window[1] <= budget_height:
            break
        cell -= 1
    return cell, max(1, cell // 6)


def window_size(width: int, height: int, cell: int) -> tuple[int, int]:
    """Return the window size a grid needs, status bar included.

    Args:
        width: Number of cells per row.
        height: Number of rows.
        cell: Pixel size of one cell.

    Returns:
        A ``(width, height)`` pair in pixels.
    """
    wall = max(1, cell // 6)
    return width * cell + wall, height * cell + wall + STATUS_HEIGHT


def window_budget(screen_width: int, screen_height: int) -> tuple[int, int]:
    """Return the largest window size that safely fits on the screen.

    A window larger than the screen gets resized by the window manager,
    and MiniLibX 2.2 never rebuilds its Vulkan swapchain afterwards, so
    the window stays black for the rest of the run. Leaving room for the
    title bar and for panels keeps the window at the size we asked for.

    Args:
        screen_width: Screen width reported by MiniLibX, or 0 if unknown.
        screen_height: Screen height reported by MiniLibX, or 0 if unknown.

    Returns:
        A ``(width, height)`` budget in pixels.
    """
    if screen_width <= 0 or screen_height <= 0:
        return MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT
    return (
        min(MAX_WINDOW_WIDTH, max(MIN_CELL, screen_width - SCREEN_MARGIN_X)),
        min(MAX_WINDOW_HEIGHT, max(MIN_CELL, screen_height - SCREEN_MARGIN_Y)),
    )


def _pixel(colour: int, depth: int, image_format: int) -> bytes:
    """Encode *colour* as the raw bytes of one fully opaque pixel.

    Args:
        colour: The colour as 0xRRGGBB.
        depth: Number of bytes per pixel.
        image_format: Byte layout, ``FORMAT_BGRA`` or ``FORMAT_ARGB``.

    Returns:
        The pixel, alpha included. Alpha is opacity in MiniLibX 2.2, so
        leaving it at zero would make the whole image invisible.
    """
    red = colour >> 16 & 0xFF
    green = colour >> 8 & 0xFF
    blue = colour & 0xFF
    if image_format == FORMAT_ARGB:
        order = (OPAQUE, red, green, blue)
    else:
        order = (blue, green, red, OPAQUE)
    return bytes(order[:depth])


class Painter:
    """Fills rectangles into a raw MiniLibX image buffer."""

    def __init__(
        self, buffer: Any, size_line: int, bits: int, image_format: int
    ) -> None:
        """Store the buffer and its geometry.

        Args:
            buffer: Writable bytes-like image data.
            size_line: Number of bytes per image row.
            bits: Bits per pixel, as reported by MiniLibX.
            image_format: 0 for B, G, R, A bytes; 1 for A, R, G, B.
        """
        self.buffer = buffer
        self.size_line = size_line
        self.depth = max(1, bits // 8)
        self.image_format = image_format

    def rect(
        self, x: int, y: int, width: int, height: int, colour: int
    ) -> None:
        """Fill a rectangle, clipping anything outside the buffer."""
        if width <= 0 or height <= 0:
            return
        row = _pixel(colour, self.depth, self.image_format) * width
        span = len(row)
        for line in range(y, y + height):
            start = line * self.size_line + x * self.depth
            if start < 0 or start + span > len(self.buffer):
                continue
            self.buffer[start:start + span] = row


def paint_scene(
    painter: Painter,
    scene: Scene,
    theme: Theme,
    show_path: bool,
    cell: int,
    wall: int,
) -> None:
    """Draw *scene* into the buffer behind *painter*.

    Args:
        painter: The target image.
        scene: The maze to draw.
        theme: The active colour scheme.
        show_path: Whether the solution path is highlighted.
        cell: Pixel size of one cell, walls included.
        wall: Pixel thickness of a wall.
    """
    inner = cell - wall
    painter.rect(
        0, 0, scene.width * cell + wall, scene.height * cell + wall,
        theme.wall,
    )
    for y in range(scene.height):
        for x in range(scene.width):
            if (x, y) in scene.pattern:
                continue
            colour = scene.cell_colour(x, y, theme, show_path)
            left = x * cell + wall
            top = y * cell + wall
            painter.rect(left, top, inner, inner, colour)
            walls = scene.grid[y][x]
            if not walls & EAST and x + 1 < scene.width:
                painter.rect((x + 1) * cell, top, wall, inner, colour)
            if not walls & SOUTH and y + 1 < scene.height:
                painter.rect(left, (y + 1) * cell, inner, wall, colour)
    for x, y in scene.pattern:
        painter.rect(
            x * cell + wall, y * cell + wall, inner, inner, theme.pattern,
        )


class MazeWindow:
    """A MiniLibX window showing a maze, with keyboard interactions.

    Keys: ``1`` regenerates, ``2`` shows or hides the shortest path,
    ``3`` cycles the colour theme, ``4`` or Escape quits.
    """

    def __init__(
        self, scene: Scene, regenerate: Callable[[], Scene], title: str
    ) -> None:
        """Open the window and draw the first frame.

        Args:
            scene: The maze to display.
            regenerate: Callable returning a freshly generated scene.
            title: Window title.

        Raises:
            RenderError: MiniLibX is missing, or no display is available.
        """
        try:
            from mlx import Mlx
        except ImportError:
            raise RenderError(
                "the 'mlx' package is not installed; install the wheel "
                "for your system from the mlx archive, or run without a "
                "graphical display."
            ) from None

        self.scene = scene
        self.regenerate = regenerate
        self.show_path = True
        self.theme_index = 0

        self.mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise RenderError(
                "cannot connect to a display; check that an X server is "
                "running and that DISPLAY is set."
            )

        # The window has to fit on the screen as it is: a window manager
        # that shrinks it leaves MiniLibX with a stale Vulkan swapchain
        # and a permanently black window.
        _, screen_width, screen_height = self.mlx.mlx_get_screen_size(
            self.mlx_ptr
        )
        budget_width, budget_height = window_budget(
            screen_width, screen_height
        )
        self.cell, self.wall = cell_size(
            scene.width, scene.height, budget_width, budget_height,
        )
        needed = window_size(scene.width, scene.height, self.cell)
        if needed[0] > budget_width or needed[1] > budget_height:
            raise RenderError(
                f"a {scene.width}x{scene.height} maze needs a "
                f"{needed[0]}x{needed[1]} window, which does not fit on "
                f"a {screen_width}x{screen_height} screen."
            )
        self.image_width = scene.width * self.cell + self.wall
        self.image_height = scene.height * self.cell + self.wall

        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, self.image_width,
            self.image_height + STATUS_HEIGHT, title,
        )
        if not self.window:
            raise RenderError("MiniLibX could not open a window.")
        self.image = self.mlx.mlx_new_image(
            self.mlx_ptr, self.image_width, self.image_height,
        )
        if not self.image:
            raise RenderError("MiniLibX could not allocate the image.")

    @property
    def theme(self) -> Theme:
        """The colour scheme currently in use."""
        return THEMES[self.theme_index % len(THEMES)]

    def _status_line(self, index: int, text: str) -> None:
        """Write one line of the status bar under the maze.

        Args:
            index: 0 for the first line, 1 for the second.
            text: The text to display.
        """
        top = self.image_height + STATUS_PADDING
        top += index * (FONT_HEIGHT + STATUS_PADDING)
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.window, STATUS_PADDING, top,
            STATUS_COLOUR, text,
        )

    def draw(self) -> None:
        """Repaint the image and push it to the window."""
        # The GPU owns the image while a frame is on screen; this waits
        # until the buffer can be written again.
        self.mlx.mlx_sync(self.mlx_ptr, SYNC_IMAGE_WRITABLE, self.image)
        buffer, bits, size_line, image_format = self.mlx.mlx_get_data_addr(
            self.image
        )
        painter = Painter(buffer, size_line, bits, image_format)
        paint_scene(
            painter, self.scene, self.theme, self.show_path,
            self.cell, self.wall,
        )
        self.mlx.mlx_clear_window(self.mlx_ptr, self.window)
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.window, self.image, 0, 0,
        )
        mode = "perfect" if self.scene.perfect else "pac-man"
        state = "on" if self.show_path else "off"
        # Every character costs one draw call, so both lines together
        # must stay under MAX_DRAWS_PER_FRAME once the maze image is
        # counted. See the module docstring.
        self._status_line(0, "1 new  2 path  3 col  4 quit")
        self._status_line(
            1,
            f"{mode} {state} {self.theme.name} {len(self.scene.path)}",
        )

    def _on_key(self, key: int, _param: object) -> None:
        """Handle one key press."""
        if key in (KEY_FOUR, KEY_ESC, KEY_Q):
            self._quit()
            return
        if key == KEY_ONE:
            # This runs inside a C callback, where an escaping exception
            # would be swallowed by ctypes after printing a traceback.
            try:
                self.scene = self.regenerate()
            except AMazeIngError as error:
                print(f"Cannot regenerate: {error}", file=sys.stderr)
                return
        elif key == KEY_TWO:
            self.show_path = not self.show_path
        elif key == KEY_THREE:
            self.theme_index += 1
        else:
            return
        self.draw()

    def _on_expose(self, _param: object = None) -> None:
        """Repaint when the window manager asks for a fresh frame."""
        if self.window:
            self.draw()

    def _on_close(self, _param: object = None) -> None:
        """Handle the window manager close button."""
        self._quit()

    def _quit(self) -> None:
        """Release MiniLibX resources and leave the event loop."""
        if self.image:
            self.mlx.mlx_destroy_image(self.mlx_ptr, self.image)
            self.image = None
        if self.window:
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
            self.window = None
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def run(self) -> None:
        """Draw the first frame and enter the MiniLibX event loop."""
        self.draw()
        self.mlx.mlx_key_hook(self.window, self._on_key, None)
        # MiniLibX 2.2 usually sends Expose only once, right after the
        # window opens; redrawing there guarantees a visible first frame.
        self.mlx.mlx_expose_hook(self.window, self._on_expose, None)
        self.mlx.mlx_hook(
            self.window, EVENT_DESTROY, 0, self._on_close, None,
        )
        self.mlx.mlx_hook(
            self.window, EVENT_CLOSE, 0, self._on_close, None,
        )
        self.mlx.mlx_loop(self.mlx_ptr)
