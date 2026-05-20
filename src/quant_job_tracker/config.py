from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "quant_job_tracker.sqlite3"
POLICY_DIR = PROJECT_ROOT / "policies"
