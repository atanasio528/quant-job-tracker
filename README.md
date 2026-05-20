# Quant Job Tracker

Local crawler, evaluator, and dashboard for front quant job applications.

V1 focuses on official career pages, US locations relevant to New York, Boston, Florida, New Jersey, and Chicago, and front quant roles suitable for an H-1B holder with 1 year of experience.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the dashboard:

```bash
qjt init-db
qjt web
```
