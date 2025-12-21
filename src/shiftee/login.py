import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .settings import ShifteeSettings
from .attendance import download_payroll_current_month, download_report_current_month


@asynccontextmanager
async def launch_browser(settings: ShifteeSettings) -> AsyncIterator[tuple[Browser, BrowserContext, Page]]:
    """Launch Playwright browser/context/page with sensible defaults."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.headless)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            yield browser, context, page
        finally:
            await context.close()
            await browser.close()


async def login(page: Page, settings: ShifteeSettings) -> None:
    """Log in using credentials from settings."""
    await page.goto(settings.login_url, wait_until="domcontentloaded")

    email_input = page.locator('input[name="email"]:visible').first
    password_input = page.locator('input[name="password"]:visible').first
    submit_button = page.locator('button[type="submit"]:visible').first

    await email_input.wait_for()
    await email_input.fill(settings.id)
    await password_input.fill(settings.password)
    await submit_button.click()

    # Wait for a post-login marker to confirm success (e.g., avatar, dashboard link).
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(500)


async def main() -> int:
    settings = ShifteeSettings()
    async with launch_browser(settings) as (_, _, page):
        await login(page, settings)
        try:
            report_destination = await download_report_current_month(page, settings)
            print(f"Downloaded report to: {report_destination}")
            payroll_destination = await download_payroll_current_month(page, settings)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] download failed: {exc}")
            return 1
        else:
            print(f"Downloaded payroll file to: {payroll_destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
