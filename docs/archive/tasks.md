# Shiftee Excel Automation Tasks

## Scope & Constraints
- Goal: log in to https://shiftee.io/ko/accounts/login, navigate to the target report, and download an Excel file automatically.
- Language: Python; automation: Playwright (preferred) or Selenium fallback only if Playwright is blocked.
- Credentials: must be pulled from a local settings file/environment (no secrets in code or git). Plan for `.env` or `config/settings.toml` read through `pydantic-settings` or similar.
- Network/captcha/MFA flows are unknown; confirm the exact login steps manually before finalizing selectors.

## Project Setup Tasks
1) Add Python tooling: `poetry` or `pip` + `requirements.txt`; include `playwright`, `pydantic-settings`, `python-dotenv`, `pytest`, `pytest-asyncio`, `ruff`, `black`.
2) Initialize repository structure: `src/` for code, `tests/` mirroring modules, `data/exports/` for downloaded files (gitignored), `config/` for templates, `logs/` for run outputs (gitignored).
3) Provide sample config (`config/settings.example.toml`) showing `SHIFTEE_ID`, `SHIFTEE_PASSWORD`, date ranges, export type, and output directory.

## Implementation Tasks
1) Authentication flow
   - Implement a `LoginClient` using Playwright. Load credentials from settings, open the login page, submit the form, and wait for a post-login landing indicator (e.g., dashboard selector). Add retries and timeout handling.
2) Navigation & filters
   - Identify URL/menus for the desired report. Expose filter inputs (date range, team, location) via settings/CLI flags. Wait for table render before export.
3) Export to Excel
   - Trigger the export action and stream the downloaded file to `data/exports/<report>-<YYYYMMDD-HHMM>.xlsx`. Ensure file name uniqueness and directory creation.
   - Validate download success (non-zero size, optional basic schema checks).
4) CLI entrypoint
   - Add `python -m src.shiftee.export --start 2024-01-01 --end 2024-01-31 --report attendance` that orchestrates login, navigation, and download. Support headless toggle and verbose logging.
5) Error handling & logging
   - Centralize logging (console + optional file). Surface actionable errors for failed login, missing selectors, or download timeouts; exit with non-zero codes.

## Testing Tasks
- Add unit tests for settings loading and path handling; integration-style tests for the export workflow using Playwright’s context recording/mocking if live login isn’t available in CI.
- Provide a dry-run mode that skips download and only verifies selectors exist to allow CI to run without credentials.

## Validation & Delivery
- Document run instructions in `README` and keep selectors/config notes in `docs/` (e.g., `docs/selectors.md`) after manual inspection of the site.
- Ensure `.env`/secrets are ignored, and confirm Playwright browsers are installed via `playwright install` in setup instructions.
