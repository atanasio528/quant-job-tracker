from quant_job_tracker import __version__
from quant_job_tracker.cli import app
from quant_job_tracker.crawler.seeds import SEEDS
from typer.testing import CliRunner


runner = CliRunner()


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_app_is_named_qjt() -> None:
    assert app.info.name == "qjt"


def test_cli_supports_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0


def test_seed_list_includes_five_large_investment_banks() -> None:
    banks = {seed.name for seed in SEEDS if seed.group == "sell_side_quant"}

    assert banks == {
        "Goldman Sachs",
        "JPMorgan Chase",
        "Morgan Stanley",
        "Citi",
        "Bank of America",
    }
