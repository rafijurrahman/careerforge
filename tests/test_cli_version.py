import pytest

from careerforge import __version__, cli


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    expected_output = f"careerforge {__version__}\n"
    # Depending on argparse version, might be in stdout or stderr
    output = captured.out or captured.err
    assert output == expected_output
    assert "0.5.1" in output
