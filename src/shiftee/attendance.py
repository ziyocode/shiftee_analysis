"""Download attendance reports."""

import logging
from datetime import date, datetime
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .settings import ShifteeSettings


async def download_report_current_month(
    page: Page,
    settings: ShifteeSettings,
    output_dir: Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Path:
    """
    From the left nav, open 리포트 -> 다운로드 -> 이번 달 -> 다운로드 and save the file.
    Uses the service-provided filename and writes to data/ by default.
    """
    logger = logging.getLogger("shiftee")
    logger.info("Starting report download")

    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Navigate to the reports page
        if settings.report_url:
            logger.debug(f"Navigating to report URL: {settings.report_url}")
            await page.goto(settings.report_url, wait_until="domcontentloaded")
            logger.debug("Report page loaded via direct URL")
        else:
            # Try to find report link by href pattern (works regardless of company ID or sidebar state)
            logger.debug("Finding '리포트' link by href pattern")
            report_link = page.locator("a[href*='/manager/report']").first
            link_count = await report_link.count()

            if link_count == 0:
                logger.debug("href pattern not found, trying text-based locator")
                report_link = page.get_by_role("link", name="리포트")
                if await report_link.count() == 0:
                    report_link = page.locator("text=리포트").first

            if settings.debug_screenshots:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"logs/screenshots/{timestamp}_report_01_before_link_click.png")
                logger.debug(f"Screenshot saved: {timestamp}_report_01_before_link_click.png")

            # Get the href and navigate directly to avoid sidebar collapsed state issues
            href = await report_link.get_attribute("href")
            if href:
                report_url = href if href.startswith("http") else f"https://shiftee.io{href}"
                logger.debug(f"Navigating directly to report URL: {report_url}")
                await page.goto(report_url, wait_until="domcontentloaded")
            else:
                logger.debug("Clicking '리포트' link")
                await report_link.click()
            await page.wait_for_load_state("networkidle")
            logger.debug("Reports page loaded")

        # Wait for page to be fully loaded
        logger.debug("Waiting for page to be fully loaded")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        logger.debug("Page fully loaded")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_report_02_page_ready.png")
            logger.debug(f"Screenshot saved: {timestamp}_report_02_page_ready.png")

        # Open the top-right download control
        logger.debug("Waiting for download button to be visible")
        download_button = page.locator('button:has-text("다운로드")').first
        await download_button.wait_for(state="visible", timeout=settings.timeout)
        logger.debug("Download button is visible")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_report_03_before_download_click.png")
            logger.debug(f"Screenshot saved: {timestamp}_report_03_before_download_click.png")

        logger.debug("Clicking download button")
        # Ensure button is enabled and clickable before clicking
        await download_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)  # Small delay for any animations

        # Use native Playwright click with force option for reliability
        await download_button.click(force=True)

        # Wait for network to be idle after click
        logger.debug("Waiting for network idle after download button click")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        logger.debug("Network is now idle")

        # Additional wait for JavaScript execution after networkidle
        logger.debug("Waiting additional 1s for JavaScript execution")
        await page.wait_for_timeout(1000)
        logger.debug("JavaScript execution wait complete")

        # Wait for modal to appear in DOM first, then become visible
        logger.debug("Waiting for export modal to be attached to DOM")
        modal = page.locator("sft-basic-export-modal").first
        await modal.wait_for(state="attached", timeout=settings.timeout)
        logger.debug("Modal attached to DOM")

        await modal.wait_for(state="visible", timeout=settings.timeout)
        logger.debug("Export modal visible")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_report_04_modal_visible.png")
            logger.debug(f"Screenshot saved: {timestamp}_report_04_modal_visible.png")

        # Open date range dropdown
        logger.debug("Clicking date range input")
        date_input = modal.locator("sft-date-range-picker input").first
        await date_input.click()

        if start_date and end_date:
            # Custom range
            range_str = f"{start_date} - {end_date}"
            logger.debug(f"Setting custom date range: {range_str}")
            await date_input.fill(range_str)
            await date_input.press("Enter")
        else:
            # Default: This month
            logger.debug("Selecting '이번 달' option")
            month_option = modal.locator("span", has_text="이번 달").first
            await month_option.click(force=True)

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_report_05_date_selected.png")
            logger.debug(f"Screenshot saved: {timestamp}_report_05_date_selected.png")

        # Trigger the final download button inside the popup/modal
        logger.debug("Clicking final download button in modal")
        confirm_download = modal.locator('button:has-text("다운로드")').first
        try:
            async with page.expect_download(timeout=settings.timeout) as dl_info:
                await confirm_download.click(force=True)
            download = await dl_info.value
            logger.debug("Download started successfully")
        except PlaywrightTimeoutError as exc:
            timeout_seconds = settings.timeout / 1000
            logger.error(f"Download timeout after {timeout_seconds}s")
            raise RuntimeError(
                f"Download did not start within {timeout_seconds}s after confirming in the report popup. "
                "Check that the modal rendered correctly and that the account has export permissions."
            ) from exc

        # 고정된 파일명 사용 (shiftee_data1.xlsx)
        filename = "shiftee_data1.xlsx"
        destination = output_dir / filename
        await download.save_as(str(destination))
        logger.info(f"Report saved to: {destination}")
        return destination

    except Exception as e:
        logger.error(f"Report download failed: {type(e).__name__}: {e}")
        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("logs/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=f"logs/screenshots/{timestamp}_ERROR_report.png")
            logger.debug(f"Error screenshot saved: {timestamp}_ERROR_report.png")

            # Save HTML content for analysis
            html_content = await page.content()
            with open(f"logs/screenshots/{timestamp}_ERROR_report.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.debug(f"HTML snapshot saved: {timestamp}_ERROR_report.html")
        raise


def _current_month_range_today() -> str:
    today = date.today()
    start = today.replace(day=1)
    return f"{start:%Y.%m.%d} - {today:%Y.%m.%d}"


async def download_payroll_current_month(
    page: Page,
    settings: ShifteeSettings,
    output_dir: Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Path:
    """
    Go to 출퇴근기록 > 목록형, open 다운로드 -> 실급여정산, set 기간 to this month (1st to today),
    select all employees, check both 근무일정 기반 / 출퇴근기록 기반, and download.
    """
    logger = logging.getLogger("shiftee")
    logger.info("Starting payroll download")

    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if settings.attendance_list_url:
            nav_url = settings.attendance_list_url
        else:
            # Find attendance list link by href pattern
            attendance_link = page.locator("a[href*='/manager/attendances/list']").first
            href = await attendance_link.get_attribute("href")
            nav_url = href if href and href.startswith("http") else f"https://shiftee.io{href}"
        logger.debug(f"Navigating to attendance list URL: {nav_url}")
        await page.goto(nav_url, wait_until="domcontentloaded")

        # Wait for page to be fully loaded
        logger.debug("Waiting for page to be fully loaded")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        logger.debug("Page fully loaded")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_payroll_01_page_loaded.png")
            logger.debug(f"Screenshot saved: {timestamp}_payroll_01_page_loaded.png")

        logger.debug("Waiting for download toggle button to be visible")
        toggle = page.locator('button.dropdown-toggle:has-text("다운로드")').first
        await toggle.wait_for(state="visible", timeout=settings.timeout)
        logger.debug("Download toggle button is visible")

        await toggle.click()
        await page.wait_for_timeout(200)

        logger.debug("Clicking '실급여정산' menu item")
        payroll_item = page.locator("a.dropdown-item", has_text="실급여정산").first
        # Use native Playwright click with force option for reliability
        await payroll_item.click(force=True)

        # Wait for network to be idle after click
        logger.debug("Waiting for network idle after payroll menu item click")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        logger.debug("Network is now idle")

        # Additional wait for JavaScript execution after networkidle
        logger.debug("Waiting additional 1s for JavaScript execution")
        await page.wait_for_timeout(1000)
        logger.debug("JavaScript execution wait complete")

        # Wait for modal to appear in DOM first, then become visible
        logger.debug("Waiting for payroll modal to be attached to DOM")
        modal = page.locator("sft-basic-export-modal").filter(has_text="실급여정산").first
        await modal.wait_for(state="attached", timeout=settings.timeout)
        logger.debug("Modal attached to DOM")

        await modal.wait_for(state="visible", timeout=settings.timeout)
        logger.debug("Payroll modal visible")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_payroll_02_modal_visible.png")
            logger.debug(f"Screenshot saved: {timestamp}_payroll_02_modal_visible.png")

        # 기간: fill explicit range (YYYY.MM.DD - YYYY.MM.DD)
        date_input = modal.locator("sft-date-range-picker input").first

        if start_date and end_date:
            range_str = f"{start_date} - {end_date}"
        else:
            range_str = _current_month_range_today()

        logger.debug(f"Setting date range: {range_str}")
        await date_input.fill(range_str)
        await date_input.press("Enter")
        await page.wait_for_timeout(200)

        # 직원들: open dropdown and select all
        logger.debug("Selecting all employees")
        employee_dropdown = modal.locator("sft-multi-select-employees .dropdown-toggle").first
        await employee_dropdown.click()
        select_all = modal.locator("sft-multi-select-employees .sft-dropdown-item-select-all").first
        await select_all.click()
        await employee_dropdown.click()

        # 실급여정산 checkboxes
        logger.debug("Checking payroll calculation options")
        for label_text in ("근무일정 기반", "출퇴근기록 기반"):
            checkbox = (
                modal.locator("label", has_text=label_text)
                .locator("input[type='checkbox']")
                .first
            )
            await checkbox.set_checked(True, force=True)
            logger.debug(f"Checked: {label_text}")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_payroll_03_before_download.png")
            logger.debug(f"Screenshot saved: {timestamp}_payroll_03_before_download.png")

        logger.debug("Clicking final download button")
        confirm_download = modal.locator('button:has-text("다운로드")').last
        try:
            async with page.expect_download(timeout=settings.timeout) as dl_info:
                await confirm_download.click()
            download = await dl_info.value
            logger.debug("Download started successfully")
        except PlaywrightTimeoutError as exc:
            timeout_seconds = settings.timeout / 1000
            logger.error(f"Download timeout after {timeout_seconds}s")
            raise RuntimeError(
                f"Download did not start within {timeout_seconds}s after confirming in the 실급여정산 modal. "
                "Check filters (기간/직원 선택) and permissions."
            ) from exc

        # 고정된 파일명 사용 (shiftee_data2.xlsx)
        filename = "shiftee_data2.xlsx"
        destination = output_dir / filename
        await download.save_as(str(destination))
        logger.info(f"Payroll saved to: {destination}")
        return destination

    except Exception as e:
        logger.error(f"Payroll download failed: {type(e).__name__}: {e}")
        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("logs/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=f"logs/screenshots/{timestamp}_ERROR_payroll.png")
            logger.debug(f"Error screenshot saved: {timestamp}_ERROR_payroll.png")

            # Save HTML content for analysis
            html_content = await page.content()
            with open(f"logs/screenshots/{timestamp}_ERROR_payroll.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.debug(f"HTML snapshot saved: {timestamp}_ERROR_payroll.html")
        raise
