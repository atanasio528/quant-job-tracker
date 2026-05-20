# Citadel Interactive Browser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional human-in-the-loop browser crawler path for Citadel official career pages when local HTTP crawling is blocked by Cloudflare.

**Architecture:** Keep the default HTTP crawler unchanged. Add an `InteractiveBrowserAdapter` wrapper that first tries the existing `GenericAdapter`, and only for Citadel/Citadel Securities falls back to a visible Selenium browser after `CareerPageBlockedError`. The Selenium session detects a Cloudflare challenge, pauses for the user to solve it manually, then returns page HTML to the existing parser/JD cleaner.

**Tech Stack:** Python, Typer CLI, BeautifulSoup, Selenium as an optional runtime dependency, pytest with fake adapters/browser sessions.

**Live Result:** Citadel detects Selenium-controlled Chrome with the "Chrome is being controlled by automated test software" banner and does not let the manual challenge complete reliably. Keep the interactive browser code as an explicit human-in-the-loop experiment, but use saved official HTML import as the practical Citadel fallback.

---

### Task 1: Interactive Adapter Unit Tests

**Files:**
- Create: `src/quant_job_tracker/crawler/interactive_browser.py`
- Modify: `tests/test_cli_pipeline.py`
- Test: `tests/test_interactive_browser.py`

- [ ] **Step 1: Write failing tests**

Add tests proving:
- blocked Citadel list pages fall back to browser HTML and parse `/careers/details/` links;
- blocked Citadel detail pages fall back to browser HTML and return cleaned JD text;
- non-Citadel blocked pages still raise `CareerPageBlockedError`;
- Cloudflare detection pauses exactly once and raises if the challenge remains after manual input.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/test_interactive_browser.py -q
```

Expected: import errors or missing-class failures.

- [ ] **Step 3: Implement adapter and Selenium session**

Create `InteractiveBrowserAdapter`, `SeleniumBrowserSession`, and `looks_like_cloudflare_challenge`. Lazy-import Selenium inside the session so normal tests and normal crawls do not require a browser.

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
pytest tests/test_interactive_browser.py -q
```

Expected: all interactive-browser unit tests pass.

### Task 2: CLI Wiring

**Files:**
- Modify: `src/quant_job_tracker/cli.py`
- Modify: `tests/test_cli_pipeline.py`

- [ ] **Step 1: Write failing CLI test**

Add a Typer test for `qjt crawl --interactive-browser` that monkeypatches `InteractiveBrowserAdapter`, verifies it is selected, and verifies `close()` is called.

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_cli_pipeline.py::test_crawl_command_uses_interactive_browser_adapter -q
```

Expected: unknown option or missing adapter wiring.

- [ ] **Step 3: Implement CLI flag**

Add `interactive_browser: bool = typer.Option(False, "--interactive-browser")` to `crawl`, pass it into `_crawl_seeds`, and close the adapter at the end if it exposes `close()`.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_cli_pipeline.py::test_crawl_command_uses_interactive_browser_adapter -q
```

Expected: pass.

### Task 3: Verification and Local Citadel Run

**Files:**
- Modify only if tests expose bugs.

- [ ] **Step 1: Run full verification**

Run:

```bash
ruff check .
pytest
```

Expected: lint clean and all tests passing.

- [ ] **Step 2: Install Selenium if missing**

Run:

```bash
python3 -m pip install selenium
```

Expected: Selenium import works with `python3 -c "import selenium; print(selenium.__version__)"`.

- [ ] **Step 3: Run the top-five crawl with user help**

Run:

```bash
qjt crawl --limit 5 --interactive-browser
```

Expected: if Citadel shows Cloudflare, the CLI asks the user to solve it manually. After the user presses Enter in the terminal, the crawler continues and stores only official Citadel detail jobs.

Observed: Citadel kept the Cloudflare challenge active in Selenium Chrome. Do not add stealth flags or automated challenge clicking.

### Task 4: Saved Official HTML Import Fallback

**Files:**
- Modify: `src/quant_job_tracker/cli.py`
- Modify: `tests/test_cli_pipeline.py`

- [ ] **Step 1: Write failing import test**

Add a Typer test for `qjt import-saved-html --company Citadel --url <official-url> --html <saved-file>`. The fixture should contain a Citadel `/careers/details/` link and assert that the job is stored with the official URL, parsed title, parsed location, and a `manual_import` run record.

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
pytest tests/test_cli_pipeline.py::test_import_saved_html_stores_jobs_from_official_listing -q
```

Expected: unknown command failure.

- [ ] **Step 3: Implement import command**

Add `import_saved_html()` to `src/quant_job_tracker/cli.py`. It should read the saved HTML, parse cards with the existing `GenericAdapter.parse_cards()`, store kept cards with `upsert_crawled_job()`, and record a `Run(kind="manual_import")`.

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
pytest tests/test_cli_pipeline.py::test_import_saved_html_stores_jobs_from_official_listing -q
```

Expected: pass.
