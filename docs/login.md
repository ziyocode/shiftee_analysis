# Shiftee Login Automation

## Prerequisites
- Install deps: `pip install -r requirements.txt`
- Install browser: `python -m playwright install chromium`
- Add credentials in `.env` or `config/settings.toml` using `config/settings.example.toml` as a template.

## Run a login attempt
- Headless (default): `python -m src.shiftee`
- Show browser: `SHIFTEE_HEADLESS=false python -m src.shiftee`

## Notes
- Login selectors now target visible email/password inputs; adjust only if the page changes.
- After login, the script opens the 리포트 view, clicks 다운로드, sets 기간 to 이번 달, and confirms 다운로드. Update `src/shiftee/attendance.py` if the UI changes.
- No secrets should be committed—keep real credentials in untracked files or environment variables.
