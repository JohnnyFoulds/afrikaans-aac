#!/usr/bin/env python3
"""
cowboard — a sticky-note board in your terminal, powered by cowsay and Textual.

Usage:
    python3 cowboard.py

Commands (typed in the bottom input bar):
    /<figure>[color] <text>

    <figure>  = any cowsay figure name (tux, dragon, elephant, …) or 'random'
    [color]   = optional single-letter suffix:
                  g=green  r=red  b=blue  y=yellow  (none=default white)
    <text>    = the message to display

Examples:
    /tux Hello world          → white tux note
    /tuxg What is ATT?        → green tux note
    /dragonr URGENT           → red dragon note
    /random Surprise me       → random figure, default colour
    /randomg Lucky green      → random figure, green

Click any note to dismiss it.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
import uuid
import warnings
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Textual imports — fail gracefully with a helpful message
# ---------------------------------------------------------------------------
try:
    from textual.app import App, ComposeResult
    from textual.css.query import NoMatches
    from textual.widgets import Input, Label, Static
    from textual.widget import Widget
    from textual import events
    from textual.geometry import Size
except ImportError:
    sys.exit(
        "textual is required.  Install it with:\n"
        "    pip install textual\n"
        "or, in the afrikaans-aac conda env:\n"
        "    /opt/homebrew/Caskroom/miniconda/base/envs/afrikaans-aac/bin/pip install textual"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PERSISTENCE_FILE = Path.home() / ".cowboard.json"

INPUT_BAR_HEIGHT = 3          # rows reserved at the bottom
MIN_NOTE_GAP = 1              # minimum blank columns between notes
RANDOM_PLACEMENT_ATTEMPTS = 5 # number of random positions tried before fallback

COLOR_MAP: dict[str, str] = {
    "g": "green",
    "r": "red",
    "b": "blue",
    "y": "yellow",
}

COLOR_STYLE: dict[str, str] = {
    "green":   "bold green",
    "red":     "bold red",
    "blue":    "bold blue",
    "yellow":  "bold yellow",
    "default": "white",
}

# ---------------------------------------------------------------------------
# Cowsay helpers
# ---------------------------------------------------------------------------

def _cowsay_figures() -> list[str]:
    """Return the list of available cowsay figures (parsed from --list)."""
    try:
        result = subprocess.run(
            ["cowsay", "--list"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        # cowsay --list output is just figure names, one per line
        return [ln.strip() for ln in lines if ln.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _run_cowsay(figure: str, text: str) -> str | None:
    """
    Run cowsay and return the output string, or None on failure.
    Returns None if cowsay is not installed or if the figure is unknown.
    """
    try:
        result = subprocess.run(
            ["cowsay", "-f", figure, text],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def _dimensions(rendered: str) -> tuple[int, int]:
    """Return (width, height) of a rendered cowsay string."""
    lines = rendered.splitlines()
    height = len(lines)
    width = max((len(ln) for ln in lines), default=0)
    return width, height


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

def parse_command(raw: str) -> tuple[str, str, str] | None:
    """
    Parse a raw command string of the form  /<figure>[color] <text>.

    Returns (figure, color_name, text)  or  None if the format is wrong.

    color_name is one of: "green", "red", "blue", "yellow", "default".
    """
    raw = raw.strip()
    if not raw.startswith("/"):
        return None

    raw = raw[1:]  # strip leading /

    if " " not in raw:
        # No text portion → invalid
        return None

    figure_part, _, text = raw.partition(" ")
    text = text.strip()
    if not text:
        return None

    # Check if last character of figure_part is a color suffix
    if figure_part and figure_part[-1] in COLOR_MAP:
        color_char = figure_part[-1]
        figure = figure_part[:-1]
        color = COLOR_MAP[color_char]
    else:
        figure = figure_part
        color = "default"

    if not figure:
        return None

    return figure, color, text


# ---------------------------------------------------------------------------
# Placement logic
# ---------------------------------------------------------------------------

class OccupancyGrid:
    """
    Tracks which (row, col) character cells are occupied by notes.
    Each note occupies a rectangle of cells including a 1-cell border gap.
    """

    def __init__(self) -> None:
        self._cells: set[tuple[int, int]] = set()

    def _rect(self, x: int, y: int, w: int, h: int) -> set[tuple[int, int]]:
        """Return all cells covered by a note rectangle plus a MIN_NOTE_GAP border."""
        cells: set[tuple[int, int]] = set()
        for row in range(y - MIN_NOTE_GAP, y + h + MIN_NOTE_GAP):
            for col in range(x - MIN_NOTE_GAP, x + w + MIN_NOTE_GAP):
                cells.add((row, col))
        return cells

    def fits(self, x: int, y: int, w: int, h: int, canvas_w: int, canvas_h: int) -> bool:
        """Return True if the note fits on-canvas and doesn't overlap occupied cells."""
        if x < 0 or y < 0:
            return False
        if x + w > canvas_w or y + h > canvas_h:
            return False
        return self._rect(x, y, w, h).isdisjoint(self._cells)

    def mark(self, x: int, y: int, w: int, h: int) -> None:
        """Mark a note's cells as occupied."""
        self._cells |= self._rect(x, y, w, h)

    def unmark(self, x: int, y: int, w: int, h: int) -> None:
        """Free a note's cells."""
        self._cells -= self._rect(x, y, w, h)

    def find_position(
        self, w: int, h: int, canvas_w: int, canvas_h: int
    ) -> tuple[int, int] | None:
        """
        Find a position for a note of size (w, h) on a canvas of (canvas_w, canvas_h).

        Strategy:
          1. Try RANDOM_PLACEMENT_ATTEMPTS random positions.
          2. Fall back to scanning top-left for the first gap that fits.

        Returns (x, y) or None if no position could be found.
        """
        if canvas_w < w or canvas_h < h:
            return None

        max_x = canvas_w - w
        max_y = canvas_h - h

        # Random attempts
        for _ in range(RANDOM_PLACEMENT_ATTEMPTS):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            if self.fits(x, y, w, h, canvas_w, canvas_h):
                return x, y

        # Deterministic scan fallback
        for row in range(max_y + 1):
            for col in range(max_x + 1):
                if self.fits(col, row, w, h, canvas_w, canvas_h):
                    return col, row

        return None  # Canvas is full


# ---------------------------------------------------------------------------
# Note data model
# ---------------------------------------------------------------------------

def load_notes(path: Path) -> list[dict[str, Any]]:
    """Load notes from the persistence file.  Returns [] on any error."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            warnings.warn(f"{path}: unexpected format (not a list); starting fresh")
            return []
        return data
    except (json.JSONDecodeError, OSError) as exc:
        warnings.warn(f"{path}: {exc}; starting fresh")
        return []


def save_notes(path: Path, notes: list[dict[str, Any]]) -> None:
    """Write notes to the persistence file."""
    try:
        path.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        warnings.warn(f"Could not save notes to {path}: {exc}")


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class NoteWidget(Static):
    """
    A single sticky note rendered as a cowsay output block.

    Clicking the note dismisses it.
    """

    DEFAULT_CSS = """
    NoteWidget {
        position: absolute;
        background: transparent;
    }
    """

    def __init__(self, note_data: dict[str, Any]) -> None:
        self._note_data = note_data
        color_name = note_data.get("color", "default")
        style = COLOR_STYLE.get(color_name, COLOR_STYLE["default"])
        rendered = note_data["rendered"]
        super().__init__(rendered, markup=False)
        self.styles.color = style
        note_id = note_data["id"]
        self.id = f"note_{note_id.replace('-', '_')}"

    @property
    def note_id(self) -> str:
        return self._note_data["id"]

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.app.dismiss_note(self.note_id)  # type: ignore[attr-defined]


class Canvas(Widget):
    """
    The full-screen canvas that holds all note widgets.
    Notes are positioned absolutely (styles.offset).
    """

    DEFAULT_CSS = """
    Canvas {
        width: 1fr;
        height: 1fr;
        overflow: hidden hidden;
        border: none;
    }
    """

    def render(self):
        return ""

    def compose(self) -> ComposeResult:
        yield from ()  # notes are added dynamically via mount()


class InputBar(Widget):
    """
    The two-row bar at the bottom of the screen.
    Contains the command Input and an error/status Label.
    """

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        width: 1fr;
        layout: vertical;
        border-top: solid $primary-darken-3;
    }
    InputBar Input {
        height: 1;
        border: none;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    InputBar Input:focus {
        border: none;
        background: $surface;
    }
    InputBar #status {
        height: 1;
        padding: 0 1;
        text-style: italic;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="❯")
        yield Label("", id="status")

    def set_status(self, message: str, is_error: bool = False) -> None:
        label = self.query_one("#status", Label)
        label.update(message)
        if is_error:
            label.styles.color = "red"
        else:
            label.styles.color = "green"
        self.app.set_timer(2.0, lambda: label.update(""))  # type: ignore[attr-defined]

    def clear_status(self) -> None:
        try:
            self.query_one("#status", Label).update("")
        except NoMatches:
            pass


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class CowboardApp(App):
    """Sticky-note board powered by cowsay."""

    TITLE = "cowboard"
    SUB_TITLE = "/<figure>[g|r|b|y] <text>  •  click a note to dismiss it  •  Ctrl+C to quit"

    DEFAULT_CSS = """
    Screen {
        layout: vertical;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._notes: list[dict[str, Any]] = []
        self._grid = OccupancyGrid()
        self._figures: set[str] = set(_cowsay_figures())
        self._cowsay_available = bool(self._figures)

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Canvas()
        yield InputBar()

    def on_mount(self) -> None:
        """Load persisted notes and render them."""
        self._notes = load_notes(PERSISTENCE_FILE)
        valid_notes: list[dict[str, Any]] = []

        canvas = self.query_one(Canvas)
        canvas_w, canvas_h = self._canvas_size()

        for note in self._notes:
            x = note.get("x", 0)
            y = note.get("y", 0)
            rendered = note.get("rendered", "")
            if not rendered:
                continue
            w, h = _dimensions(rendered)
            # Mark occupied even if partially out of bounds (don't let new notes
            # collide with old positions, even if we can't fully render them)
            self._grid.mark(x, y, w, h)
            widget = NoteWidget(note)
            widget.styles.offset = (x, y)
            widget.styles.width = w
            widget.styles.height = h
            canvas.mount(widget)
            valid_notes.append(note)

        # Prune any corrupted entries that had no rendered text
        if len(valid_notes) != len(self._notes):
            self._notes = valid_notes
            save_notes(PERSISTENCE_FILE, self._notes)

        # Focus the input
        self.query_one(Input).focus()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle a command entered in the input bar."""
        raw = event.value.strip()
        event.input.clear()

        if not raw:
            return

        if not self._cowsay_available:
            self.query_one(InputBar).set_status(
                "cowsay is not installed — install it with: brew install cowsay",
                is_error=True,
            )
            return

        parsed = parse_command(raw)
        if parsed is None:
            self.query_one(InputBar).set_status(
                "Syntax: /<figure>[g|r|b|y] <text>  e.g.  /tux Hello  /dragonr URGENT",
                is_error=True,
            )
            return

        figure, color, text = parsed

        # Resolve 'random' to an actual figure
        if figure == "random":
            figure = random.choice(list(self._figures))

        # Validate the figure
        if figure not in self._figures:
            self.query_one(InputBar).set_status(
                f"Unknown figure '{figure}'.  Try: tux, dragon, elephant, vader, …",
                is_error=True,
            )
            return

        # Generate cowsay output
        rendered = _run_cowsay(figure, text)
        if rendered is None:
            self.query_one(InputBar).set_status(
                f"cowsay failed for figure '{figure}'.",
                is_error=True,
            )
            return

        # Determine dimensions and find placement
        w, h = _dimensions(rendered)
        canvas_w, canvas_h = self._canvas_size()
        pos = self._grid.find_position(w, h, canvas_w, canvas_h)

        if pos is None:
            self.query_one(InputBar).set_status(
                "Canvas is full — dismiss some notes first.",
                is_error=True,
            )
            return

        x, y = pos
        self._grid.mark(x, y, w, h)

        note_data: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "figure": figure,
            "text": text,
            "color": color,
            "x": x,
            "y": y,
            "rendered": rendered,
        }
        self._notes.append(note_data)
        save_notes(PERSISTENCE_FILE, self._notes)

        widget = NoteWidget(note_data)
        widget.styles.offset = (x, y)
        widget.styles.width = w
        widget.styles.height = h
        self.query_one(Canvas).mount(widget)

        self.query_one(InputBar).set_status(
            f"Added {figure} note ({color})",
            is_error=False,
        )

    # ------------------------------------------------------------------
    # Public API (called by NoteWidget.on_click)
    # ------------------------------------------------------------------

    def dismiss_note(self, note_id: str) -> None:
        """Remove a note from the canvas and persistence."""
        # Find note data
        note_data = next((n for n in self._notes if n["id"] == note_id), None)
        if note_data is None:
            return

        # Free occupancy
        x = note_data.get("x", 0)
        y = note_data.get("y", 0)
        rendered = note_data.get("rendered", "")
        if rendered:
            w, h = _dimensions(rendered)
            self._grid.unmark(x, y, w, h)

        # Remove from data and persist
        self._notes = [n for n in self._notes if n["id"] != note_id]
        save_notes(PERSISTENCE_FILE, self._notes)

        # Remove widget from DOM
        widget_id = f"note_{note_id.replace('-', '_')}"
        try:
            widget = self.query_one(f"#{widget_id}", NoteWidget)
            widget.remove()
        except NoMatches:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _canvas_size(self) -> tuple[int, int]:
        """
        Return (width, height) of the usable canvas area in character cells.
        Falls back to terminal size minus the input bar if the widget hasn't
        been laid out yet.
        """
        try:
            canvas = self.query_one(Canvas)
            size = canvas.size
            if size.width > 0 and size.height > 0:
                return size.width, size.height
        except NoMatches:
            pass

        # Pre-layout fallback
        w, h = self.app.size.width, self.app.size.height
        return w, max(1, h - INPUT_BAR_HEIGHT)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = CowboardApp()
    app.run()
