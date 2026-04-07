# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Automated Excel report downloader for Shiftee.io (https://shiftee.io) using Playwright for browser automation. The application logs in, navigates to specific reports, and downloads attendance/payroll data as Excel files.

## Development Setup

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Install Playwright browser
uv run playwright install chromium

# Configure credentials (required before first run)
cp config/settings.example.toml config/settings.toml
# Edit config/settings.toml or create .env with SHIFTEE_ID and SHIFTEE_PASSWORD
```

## Running the Application

```bash
# Standard headless mode (default)
uv run shiftee-analyze

# Show browser for debugging
SHIFTEE_HEADLESS=false uv run shiftee-analyze
```

The application will:
1. Log in to Shiftee.io using credentials from settings
2. Download the current month's attendance report (리포트)
3. Download the current month's payroll calculation (실급여정산) from 출퇴근기록 > 목록형
4. Save files to `data/` directory with timestamped filenames

## Architecture

### Module Organization
- **`src/shiftee/settings.py`**: Configuration management using pydantic-settings; loads from `.env` or `config/settings.toml` with `SHIFTEE_` prefix
- **`src/shiftee/login.py`**: Browser launch and authentication flow; provides `launch_browser()` context manager and `login()` function
- **`src/shiftee/attendance.py`**: Report download logic with two main functions:
  - `download_report_current_month()`: Downloads 리포트 for current month
  - `download_payroll_current_month()`: Downloads 실급여정산 with both 근무일정/출퇴근기록 options
- **`src/shiftee/__main__.py`**: CLI entrypoint that orchestrates login and downloads

### Selector Strategy
The application uses Playwright locators targeting Korean UI text (e.g., `리포트`, `다운로드`, `이번 달`). If Shiftee.io UI changes:
1. Update selectors in `attendance.py` for the affected download workflow
2. Login selectors in `login.py` target `input[name="email"]` and `input[name="password"]`
3. Test changes with `SHIFTEE_HEADLESS=false` to observe browser behavior

### Configuration System
Settings support environment variables (`.env`) or TOML (`config/settings.toml`). All settings use `SHIFTEE_` prefix:
- `SHIFTEE_ID`: Login email (required)
- `SHIFTEE_PASSWORD`: Login password (required)
- `SHIFTEE_HEADLESS`: Run browser in headless mode (default: true)
- `SHIFTEE_BASE_URL`: Shiftee base URL (default: "https://shiftee.io")
- `SHIFTEE_CALENDAR_URL`, `SHIFTEE_REPORT_URL`, `SHIFTEE_ATTENDANCE_LIST_URL`: Direct URLs for specific pages

### Output Management
Downloaded files are saved to `data/` with server-provided filenames (e.g., `SHIFTEE-REALTIME-REPORT-20251201-20251231.xlsx`). The `data/` directory is created automatically but should be gitignored for credential safety.

## Testing Notes

Currently no automated tests exist. For manual testing:
- Use `SHIFTEE_HEADLESS=false` to observe browser behavior
- Verify selectors after any Shiftee UI updates
- Test both report and payroll downloads complete successfully
- Confirm files are saved with correct filenames and non-zero size

## Security

- Never commit `.env`, `config/settings.toml`, or any files in `data/` containing credentials or sensitive data
- Credentials are loaded via pydantic-settings and never hardcoded
- Use environment variables in CI/CD environments

## Common Issues

- **"Download did not start within 90s"**: Check that modal rendered correctly and account has export permissions; may indicate UI changes requiring selector updates
- **Login fails**: Verify credentials in settings; check for captcha/MFA requirements (not currently supported)
- **Playwright browser not found**: Run `uv run playwright install chromium`
