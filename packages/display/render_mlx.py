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

from typing import Any, Callable, Final

from errors import RenderError
from packages.presentation.view import Scene, Theme, THEMES

MAX_WINDOW_WIDTH: Final[int] = 2800
MAX_WINDOW_HEIGHT: Final[int] = 1780
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

        try:
            self.mlx = Mlx()
            self.mlx_ptr = self.mlx.mlx_init()
        except Exception as error:
            raise RenderError(
                f"cannot initialize MiniLibX: {error}"
            ) from None
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
        self.image_width, self.image_height = window_size(
            scene.width, scene.height, self.cell,
        )
        if (
            self.image_width > budget_width
            or self.image_height > budget_height
        ):
            raise RenderError(
                f"the requested maze window {self.image_width}x"
                f"{self.image_height} does not fit the available "
                f"{budget_width}x{budget_height} screen budget; reduce "
                "WIDTH or HEIGHT."
            )
        self.window = self.mlx.mlx_new_window(
            self.mlx_ptr, self.image_width,
            self.image_height, title,
        )
        if not self.window:
            raise RenderError("cannot create a MiniLibX window.")
        self.image = self.mlx.mlx_new_image(
            self.mlx_ptr, self.image_width, self.image_height,
        )
        if not self.image:
            raise RenderError("cannot create a MiniLibX image.")

        self._render()
        self._register_hooks()

    @property
    def theme(self) -> Theme:
        """Return the current colour theme."""
        return THEMES[self.theme_index]

    def _draw_status(self, top: int) -> None:
        """Draw the title and control hints in the top-left corner."""
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.window, STATUS_PADDING, top,
            STATUS_COLOUR, f"{self.theme.name.upper()} theme",
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.window, STATUS_PADDING, top + FONT_HEIGHT,
            STATUS_COLOUR, "1 regen  2 path  3 theme  4/ESC quit",
        )

    def _render(self) -> None:
        """Redraw the image and the text overlay."""
        self.mlx.mlx_sync(self.mlx_ptr, SYNC_IMAGE_WRITABLE, self.image)
        buffer, bits, size_line, image_format = self.mlx.mlx_get_data_addr(
            self.image
        )
        painter = Painter(buffer, size_line, bits, image_format)
        paint_scene(
            painter, self.scene, self.theme, self.show_path, self.cell,
            self.wall,
        )
        self.mlx.mlx_clear_window(self.mlx_ptr, self.window)
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.window, self.image, 0, 0,
        )
        status_top = (
            self.scene.height * self.cell + self.wall + STATUS_PADDING
        )
        self._draw_status(status_top)

    def _redraw(self) -> None:
        """Refresh the window after a state change."""
        self._render()

    def _next_theme(self) -> None:
        """Cycle to the next colour theme."""
        self.theme_index = (self.theme_index + 1) % len(THEMES)

    def _on_key(self, key: int, _data: Any) -> int:
        """Handle keyboard shortcuts."""
        if key in (KEY_FOUR, KEY_ESC, KEY_Q):
            self._close()
            return 0
        if key == KEY_ONE:
            self.scene = self.regenerate()
            self._redraw()
        elif key == KEY_TWO:
            self.show_path = not self.show_path
            self._redraw()
        elif key == KEY_THREE:
            self._next_theme()
            self._redraw()
        return 0

    def _on_expose(self, _data: Any) -> int:
        """Redraw after the window is exposed."""
        self._redraw()
        return 0

    def _on_close(self, _data: Any) -> int:
        """Handle the window manager close button."""
        self._close()
        return 0

    def _close(self) -> None:
        """Tear down MiniLibX resources and exit the event loop."""
        if getattr(self, "image", None):
            self.mlx.mlx_destroy_image(self.mlx_ptr, self.image)
            self.image = None
        if getattr(self, "window", None):
            self.mlx.mlx_destroy_window(self.mlx_ptr, self.window)
            self.window = None
        self.mlx.mlx_loop_exit(self.mlx_ptr)

    def _register_hooks(self) -> None:
        """Bind the event handlers used by the window."""
        self.mlx.mlx_key_hook(self.window, self._on_key, None)
        self.mlx.mlx_expose_hook(self.window, self._on_expose, None)
        self.mlx.mlx_hook(
            self.window, EVENT_DESTROY, 0, self._on_close, None
        )
        self.mlx.mlx_hook(
            self.window, EVENT_CLOSE, 0, self._on_close, None
        )

    def run(self) -> None:
        """Start the MiniLibX event loop."""
        self.mlx.mlx_loop(self.mlx_ptr)
