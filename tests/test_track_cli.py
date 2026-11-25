"""
CLI tests for `forge track` subcommands, TUI smoke pilot test, and missing [tui] hint.
"""

import asyncio
import json
import sys
from unittest.mock import patch

import pytest

from careerforge.cli import main
from careerforge.core.store import CareerStore
from careerforge.tui import TrackBoardApp


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["forge"] + argv)
    with pytest.raises(SystemExit) as exc:
        try:
            main()
        except SystemExit:
            raise
        else:
            raise SystemExit(0)
    return exc.value.code


def test_track_cli_end_to_end(tmp_path, monkeypatch, capsys, socket_disabled=None):
    db_file = str(tmp_path / "cli_track.db")
    monkeypatch.setenv("CAREERFORGE_DB", db_file)

    cv_file = tmp_path / "cv.pdf"
    cv_file.write_bytes(b"%PDF-1.4 test")

    # 1. track add --manual --json
    code = _run_cli(
        [
            "track",
            "add",
            "--manual",
            "--company",
            "Northwind",
            "--title",
            "Data Analyst",
            "--stage",
            "saved",
            "--cv",
            str(cv_file),
            "--jd",
            "SQL and Power BI role.",
            "--json",
        ],
        monkeypatch,
    )
    assert code == 0
    out = capsys.readouterr().out
    app_data = json.loads(out)
    app_id = app_data["id"]
    assert app_data["company"] == "Northwind"
    assert len(app_data["cv_sha256"]) == 64

    # 2. track move
    code = _run_cli(["track", "move", str(app_id), "applied", "--note", "Applied online", "--json"], monkeypatch)
    assert code == 0
    moved = json.loads(capsys.readouterr().out)
    assert moved["stage"] == "applied"

    # 3. track note
    code = _run_cli(["track", "note", str(app_id), "Followed up via LinkedIn", "--json"], monkeypatch)
    assert code == 0
    noted = json.loads(capsys.readouterr().out)
    assert any("Followed up" in e["detail"] for e in noted["events"])

    # 4. track list --stage applied --json
    code = _run_cli(["track", "list", "--stage", "applied", "--json"], monkeypatch)
    assert code == 0
    listed = json.loads(capsys.readouterr().out)
    assert len(listed) == 1
    assert listed[0]["id"] == app_id

    # 5. track show
    code = _run_cli(["track", "show", str(app_id), "--json"], monkeypatch)
    assert code == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["jd_snapshot"] == "SQL and Power BI role."

    # 6. track export --csv
    csv_path = tmp_path / "export.csv"
    code = _run_cli(["track", "export", "--csv", "--out", str(csv_path)], monkeypatch)
    assert code == 0
    capsys.readouterr()
    assert "Northwind" in csv_path.read_text(encoding="utf-8")


def test_track_cli_error_exit_codes(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CAREERFORGE_DB", str(tmp_path / "err.db"))

    # Missing ID -> exit 2
    code = _run_cli(["track", "show", "999"], monkeypatch)
    assert code == 2
    assert "not found" in capsys.readouterr().err

    # Invalid stage -> exit 2
    code = _run_cli(["track", "list", "--stage", "bogus"], monkeypatch)
    assert code == 2
    assert "Invalid stage" in capsys.readouterr().err

    # Export without format flag -> exit 2
    code = _run_cli(["track", "export"], monkeypatch)
    assert code == 2
    assert "Specify either --csv or --md" in capsys.readouterr().err

    # Missing profile.yaml -> clean error with forge init hint (exit 2)
    monkeypatch.chdir(tmp_path)
    code = _run_cli(["match", "--jd", "Python SQL"], monkeypatch)
    assert code == 2
    assert "forge init" in capsys.readouterr().err


def test_track_board_missing_tui_hint(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CAREERFORGE_DB", str(tmp_path / "notui.db"))
    with patch.dict(sys.modules, {"careerforge.tui": None}):
        code = _run_cli(["track", "board"], monkeypatch)
    assert code == 2
    err = capsys.readouterr().err
    assert "pip install careerforge[tui]" in err


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_track_board_tui_smoke_pilot(tmp_path):
    """Runs Textual pilot smoke test (loopback only for asyncio self-pipe; all external hosts blocked)."""
    db_file = str(tmp_path / "tui_smoke.db")
    store = CareerStore(db_path=db_file)
    app_rec = store.add_application(manual=True, company="BetaCo", title="Platform Eng", stage="saved")

    async def _run_pilot():
        app = TrackBoardApp(db_path=db_file)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Move card right from saved -> applied
            await pilot.press("right_square_bracket")
            await pilot.pause()
            # Toggle detail pane on Enter
            await pilot.press("enter")
            await pilot.pause()
            assert app.details_visible is True
            await pilot.press("q")

    asyncio.run(_run_pilot())
    updated = store.get_application(app_rec["id"])
    assert updated is not None
    assert updated["stage"] == "applied"
    assert any("saved -> applied" in e["detail"] for e in updated["events"])
