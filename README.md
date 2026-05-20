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

## Provider-Blocked Pages

Some official career pages, including Citadel, may block automated HTTP or Selenium
browsers. Do not use unofficial mirrors. Open the official page in your normal
browser, solve the security check manually, save the page as HTML, then import it:

```bash
qjt import-saved-html \
  --company "Citadel" \
  --url "https://www.citadel.com/careers/open-opportunities/" \
  --html ~/Downloads/citadel-open-opportunities.html
qjt eval-pending
```
