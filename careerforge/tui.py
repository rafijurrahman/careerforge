"""
Optional Textual Kanban Board TUI for CareerForge (`forge track board`).
Requires the optional extra: `pip install careerforge[tui]`.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Static

try:
    from careerforge.core.store import VALID_STAGES, CareerStore
except ImportError:
    from core.store import VALID_STAGES, CareerStore


class TrackBoardApp(App):
    """Offline Kanban board for managing job applications across pipeline stages."""

    TITLE = "CareerForge Track Board"
    SUB_TITLE = "Arrows/HJKL: Navigate | [ / ] or Shift+Arrows: Move Stage | Enter: Details | Q: Quit"

    CSS = """
    Screen {
        layout: vertical;
    }
    #board {
        height: 1fr;
        layout: horizontal;
    }
    .stage-col {
        width: 1fr;
        height: 1fr;
        border: solid #475569;
        padding: 0 1;
        margin: 0;
    }
    .stage-col.active-col {
        border: heavy #38bdf8;
    }
    .col-header {
        text-style: bold;
        color: #f8fafc;
        background: #1e293b;
        width: 1fr;
        padding: 0 1;
        margin-bottom: 1;
    }
    .card {
        border: round #64748b;
        padding: 0 1;
        margin-bottom: 1;
        width: 1fr;
    }
    .card.active-card {
        border: double #f59e0b;
        background: #1e293b;
    }
    #detail-pane {
        height: auto;
        max-height: 12;
        border: solid #10b981;
        padding: 0 1;
        background: #0f172a;
        display: none;
    }
    #detail-pane.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("left,h", "col_left", "Prev Stage"),
        Binding("right,l", "col_right", "Next Stage"),
        Binding("up,k", "card_up", "Prev Card"),
        Binding("down,j", "card_down", "Next Card"),
        Binding("left_square_bracket,shift+left", "move_left", "Move Left"),
        Binding("right_square_bracket,shift+right", "move_right", "Move Right"),
        Binding("enter", "toggle_details", "Details"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: Optional[str] = None) -> None:
        super().__init__()
        self.store = CareerStore(db_path=db_path)
        self.selected_stage_idx: int = 0
        self.selected_card_idx: int = 0
        self.details_visible: bool = False
        self._by_stage: Dict[str, List[dict]] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="board"):
            for stage in VALID_STAGES:
                with VerticalScroll(id=f"col-{stage}", classes="stage-col"):
                    yield Static(stage.upper(), id=f"header-{stage}", classes="col-header")
                    yield Static("", id=f"body-{stage}")
        yield Static("", id="detail-pane")
        yield Footer()

    def on_mount(self) -> None:
        self._load_data()
        # Focus the first stage that actually has cards if saved is empty
        if not self._by_stage.get(VALID_STAGES[self.selected_stage_idx]):
            for idx, st in enumerate(VALID_STAGES):
                if self._by_stage.get(st):
                    self.selected_stage_idx = idx
                    break
        self._render_board()

    def _load_data(self) -> None:
        apps = self.store.list_applications()
        self._by_stage = {st: [] for st in VALID_STAGES}
        for app in apps:
            st = app.get("stage", "saved")
            if st in self._by_stage:
                self._by_stage[st].append(app)

    def _current_stage(self) -> str:
        return VALID_STAGES[self.selected_stage_idx]

    def _selected_app(self) -> Optional[dict]:
        cards = self._by_stage.get(self._current_stage(), [])
        if not cards:
            return None
        idx = max(0, min(self.selected_card_idx, len(cards) - 1))
        self.selected_card_idx = idx
        return cards[idx]

    def _render_board(self) -> None:
        for idx, stage in enumerate(VALID_STAGES):
            col_widget = self.query_one(f"#col-{stage}", VerticalScroll)
            header_widget = self.query_one(f"#header-{stage}", Static)
            body_widget = self.query_one(f"#body-{stage}", Static)

            cards = self._by_stage.get(stage, [])
            is_active_col = idx == self.selected_stage_idx
            col_widget.set_class(is_active_col, "active-col")
            header_widget.update(f"{stage.upper()} ({len(cards)})")

            if not cards:
                body_widget.update("[dim](empty)[/dim]")
                continue

            lines: List[str] = []
            for c_idx, card in enumerate(cards):
                marker = ">> " if (is_active_col and c_idx == self.selected_card_idx) else "   "
                company = card.get("company", "Unknown")
                title = card.get("title", "")
                line = f"{marker}#{card['id']} {company}: {title}"
                if is_active_col and c_idx == self.selected_card_idx:
                    lines.append(f"[bold yellow]{line}[/bold yellow]")
                else:
                    lines.append(line)
            body_widget.update("\n".join(lines))

        detail_widget = self.query_one("#detail-pane", Static)
        app = self._selected_app()
        if self.details_visible and app is not None:
            full = self.store.get_application(app["id"]) or app
            events = full.get("events", [])
            last_ev = events[-1]["detail"] if events else "-"
            applied_dt = (full.get("applied_at") or "-")[:10]
            cv_hash = (full.get("cv_sha256") or "-")[:12]
            detail_widget.set_class(True, "visible")
            detail_widget.update(
                f"[bold cyan]Application #{full['id']}[/bold cyan] | "
                f"[bold]{full.get('title', '')}[/bold] @ {full.get('company', '')} "
                f"([green]{full.get('stage', '')}[/green])\n"
                f"Applied: {applied_dt} | Source: {full.get('source', '')} | CV SHA-256: {cv_hash}\n"
                f"URL: {full.get('url') or '-'}\n"
                f"Last Event: {last_ev} | Notes: {full.get('notes') or '-'}"
            )
        else:
            detail_widget.set_class(False, "visible")

    def action_col_left(self) -> None:
        self.selected_stage_idx = (self.selected_stage_idx - 1) % len(VALID_STAGES)
        self.selected_card_idx = 0
        self._render_board()

    def action_col_right(self) -> None:
        self.selected_stage_idx = (self.selected_stage_idx + 1) % len(VALID_STAGES)
        self.selected_card_idx = 0
        self._render_board()

    def action_card_up(self) -> None:
        cards = self._by_stage.get(self._current_stage(), [])
        if cards:
            self.selected_card_idx = max(0, self.selected_card_idx - 1)
        self._render_board()

    def action_card_down(self) -> None:
        cards = self._by_stage.get(self._current_stage(), [])
        if cards:
            self.selected_card_idx = min(len(cards) - 1, self.selected_card_idx + 1)
        self._render_board()

    def _move_selected(self, delta: int) -> None:
        app = self._selected_app()
        if app is None:
            return
        new_idx = self.selected_stage_idx + delta
        if not (0 <= new_idx < len(VALID_STAGES)):
            return
        target_stage = VALID_STAGES[new_idx]
        self.store.move_application(app["id"], target_stage)
        self._load_data()
        self.selected_stage_idx = new_idx
        cards_in_new = self._by_stage.get(target_stage, [])
        self.selected_card_idx = next(
            (i for i, c in enumerate(cards_in_new) if c["id"] == app["id"]),
            0,
        )
        self._render_board()

    def action_move_left(self) -> None:
        self._move_selected(-1)

    def action_move_right(self) -> None:
        self._move_selected(1)

    def action_toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        self._render_board()


def run_board_tui(db_path: Optional[str] = None) -> None:
    """Launches the interactive Kanban TUI."""
    app = TrackBoardApp(db_path=db_path)
    app.run()
