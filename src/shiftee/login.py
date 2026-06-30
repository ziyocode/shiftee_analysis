import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .settings import ShifteeSettings
from .attendance import download_payroll_current_month, download_report_current_month


# 헤드리스 봇 감지 우회용 스텔스 설정.
# Shiftee 신규 /app SPA는 자동화(navigator.webdriver 등)를 감지하면 헤드리스에서
# 부팅을 거부하고 로딩 스피너에서 멈춘다. 실제 데스크톱 Chrome처럼 위장한다.
_STEALTH_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

_STEALTH_INIT_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko','en-US','en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
window.chrome = window.chrome || { runtime: {} };
const _origQuery = navigator.permissions && navigator.permissions.query;
if (_origQuery) {
  navigator.permissions.query = (p) => (
    p && p.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : _origQuery(p)
  );
}
"""


def setup_logging(settings: ShifteeSettings) -> logging.Logger:
    """Setup logging configuration based on settings."""
    logger = logging.getLogger("shiftee")

    if settings.debug_logs:
        logger.setLevel(logging.DEBUG)

        # Create logs directory if needed
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    else:
        logger.setLevel(logging.WARNING)

    return logger


@asynccontextmanager
async def launch_browser(settings: ShifteeSettings) -> AsyncIterator[tuple[Browser, BrowserContext, Page]]:
    """Launch Playwright browser/context/page with sensible defaults."""
    logger = logging.getLogger("shiftee")
    logger.info(f"Launching browser (headless={settings.headless})")

    async with async_playwright() as p:
        launch_args = []
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
        # 자동화 감지 완화 플래그 (헤드리스 봇 감지 우회)
        launch_args.append("--disable-blink-features=AutomationControlled")

        # 헤드리스일 때는 '신규 헤드리스 모드'(--headless=new)를 사용한다.
        # 구형 헤드리스는 UA에 'HeadlessChrome'이 박히고 렌더링 경로도 달라 Shiftee
        # 신규 /app SPA가 봇으로 감지해 부팅을 거부한다(브라우저 창 표시 모드에서만
        # 동작하던 원인). 신규 헤드리스는 실제 Chrome과 거의 동일하게 동작하므로
        # 창 없이도 SPA가 정상 부팅한다. Playwright가 구형 --headless를 붙이지 않도록
        # headless=False로 띄우고 --headless=new를 직접 전달한다.
        if settings.headless:
            launch_args.append("--headless=new")
        browser = await p.chromium.launch(headless=False, args=launch_args)
        logger.debug(f"Browser launched (new-headless={settings.headless})")

        # 실제 데스크톱 브라우저처럼 보이는 컨텍스트 (신규 /app SPA 부팅 차단 방지)
        context = await browser.new_context(
            user_agent=_STEALTH_USER_AGENT,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={"width": 1920, "height": 1080},
        )
        # navigator.webdriver 등 자동화 흔적 마스킹 (모든 신규 문서에 주입)
        await context.add_init_script(_STEALTH_INIT_JS)

        # Apply timeout settings for macOS automation compatibility
        context.set_default_timeout(settings.timeout)
        context.set_default_navigation_timeout(settings.navigation_timeout)
        logger.debug(f"Timeout settings applied: {settings.timeout}ms (action), {settings.navigation_timeout}ms (navigation)")

        page = await context.new_page()
        logger.debug("New page created")

        try:
            yield browser, context, page
        finally:
            logger.debug("Closing browser")
            await context.close()
            await browser.close()
            logger.info("Browser closed")


async def login(page: Page, settings: ShifteeSettings) -> None:
    """Log in using credentials from settings."""
    logger = logging.getLogger("shiftee")
    logger.info(f"Starting login to {settings.login_url}")

    try:
        await page.goto(settings.login_url, wait_until="domcontentloaded")
        logger.debug("Login page loaded")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("logs/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=f"logs/screenshots/{timestamp}_01_login_page.png")
            logger.debug(f"Screenshot saved: {timestamp}_01_login_page.png")

        email_input = page.locator('input[name="email"]:visible').first
        password_input = page.locator('input[name="password"]:visible').first
        submit_button = page.locator('button[type="submit"]:visible').first

        logger.debug("Waiting for email input field")
        await email_input.wait_for()
        logger.debug("Filling email")
        await email_input.fill(settings.id)

        logger.debug("Filling password")
        await password_input.fill(settings.password)

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_02_before_submit.png")
            logger.debug(f"Screenshot saved: {timestamp}_02_before_submit.png")

        logger.debug("Clicking submit button")
        await submit_button.click()

        # Wait for a post-login marker to confirm success (e.g., avatar, dashboard link).
        logger.debug("Waiting for page to load after login")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_03_after_login.png")
            logger.debug(f"Screenshot saved: {timestamp}_03_after_login.png")

        logger.info("Login completed successfully")

    except Exception as e:
        logger.error(f"Login failed: {type(e).__name__}: {e}")
        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("logs/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=f"logs/screenshots/{timestamp}_ERROR_login.png")
            logger.debug(f"Error screenshot saved: {timestamp}_ERROR_login.png")

            # Save HTML content for analysis
            html_content = await page.content()
            with open(f"logs/screenshots/{timestamp}_ERROR_login.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.debug(f"HTML snapshot saved: {timestamp}_ERROR_login.html")
        raise


async def main() -> int:
    settings = ShifteeSettings()
    logger = setup_logging(settings)
    logger.info("=== Shiftee automation started ===")

    try:
        async with launch_browser(settings) as (_, _, page):
            await login(page, settings)
            try:
                report_destination = await download_report_current_month(page, settings)
                print(f"Downloaded report to: {report_destination}")
                logger.info(f"Report downloaded: {report_destination}")

                payroll_destination = await download_payroll_current_month(page, settings)
                print(f"Downloaded payroll file to: {payroll_destination}")
                logger.info(f"Payroll downloaded: {payroll_destination}")
            except Exception as exc:  # noqa: BLE001
                print(f"[error] download failed: {exc}")
                logger.error(f"Download failed: {type(exc).__name__}: {exc}", exc_info=True)
                return 1
        logger.info("=== Shiftee automation completed successfully ===")
        return 0
    except Exception as exc:
        logger.error(f"Fatal error: {type(exc).__name__}: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
