from quant_job_tracker import __version__
from quant_job_tracker.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_app_is_named_qjt() -> None:
    assert app.info.name == "qjt"


def test_cli_supports_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
