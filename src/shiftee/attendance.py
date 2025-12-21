"""Download attendance reports."""

from datetime import date
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
    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Navigate to the reports page
    if settings.report_url:
        await page.goto(settings.report_url, wait_until="domcontentloaded")
    else:
        report_link = page.get_by_role("link", name="리포트")
        if await report_link.count() == 0:
            report_link = page.locator("text=리포트").first
        await report_link.click()
        await page.wait_for_load_state("networkidle")

    await page.wait_for_timeout(1000)

    # Open the top-right download control
    download_button = page.locator('button:has-text("다운로드")').first
    await download_button.click()

    # Wait for modal to appear
    modal = page.locator("sft-basic-export-modal").first
    await modal.wait_for(state="visible", timeout=10_000)

    # Open date range dropdown
    date_input = modal.locator("sft-date-range-picker input").first
    await date_input.click()

    if start_date and end_date:
        # Custom range
        # Format: YYYY.MM.DD - YYYY.MM.DD
        range_str = f"{start_date} - {end_date}"
        await date_input.fill(range_str)
        await date_input.press("Enter")
    else:
        # Default: This month
        month_option = modal.locator("span", has_text="이번 달").first
        await month_option.evaluate("el => el.click()")

    # Trigger the final download button inside the popup/modal
    confirm_download = modal.locator('button:has-text("다운로드")').first
    try:
        async with page.expect_download(timeout=90_000) as dl_info:
            await confirm_download.evaluate("el => el.click()")
        download = await dl_info.value
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Download did not start within 90s after confirming in the report popup. "
            "Check that the modal rendered correctly and that the account has export permissions."
        ) from exc

    # 고정된 파일명 사용 (shiftee_data1.xlsx)
    filename = "shiftee_data1.xlsx"
    destination = output_dir / filename
    await download.save_as(str(destination))
    return destination


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
    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    await page.goto(settings.attendance_list_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(800)

    toggle = page.locator('button.dropdown-toggle:has-text("다운로드")').first
    await toggle.click()
    await page.wait_for_timeout(200)

    payroll_item = page.locator("a.dropdown-item", has_text="실급여정산").first
    await payroll_item.click()

    modal = page.locator("sft-basic-export-modal").filter(has_text="실급여정산").first
    await modal.wait_for(state="visible", timeout=10_000)

    # 기간: fill explicit range (YYYY.MM.DD - YYYY.MM.DD)
    date_input = modal.locator("sft-date-range-picker input").first
    
    if start_date and end_date:
        range_str = f"{start_date} - {end_date}"
    else:
        range_str = _current_month_range_today()
        
    await date_input.fill(range_str)
    await date_input.press("Enter")
    await page.wait_for_timeout(200)

    # 직원들: open dropdown and select all
    employee_dropdown = modal.locator("sft-multi-select-employees .dropdown-toggle").first
    await employee_dropdown.click()
    select_all = modal.locator("sft-multi-select-employees .sft-dropdown-item-select-all").first
    await select_all.click()
    await employee_dropdown.click()

    # 실급여정산 checkboxes
    for label_text in ("근무일정 기반", "출퇴근기록 기반"):
        checkbox = (
            modal.locator("label", has_text=label_text)
            .locator("input[type='checkbox']")
            .first
        )
        await checkbox.set_checked(True, force=True)

    confirm_download = modal.locator('button:has-text("다운로드")').last
    try:
        async with page.expect_download(timeout=90_000) as dl_info:
            await confirm_download.click()
        download = await dl_info.value
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Download did not start within 90s after confirming in the 실급여정산 modal. "
            "Check filters (기간/직원 선택) and permissions."
        ) from exc

    # 고정된 파일명 사용 (shiftee_data2.xlsx)
    filename = "shiftee_data2.xlsx"
    destination = output_dir / filename
    await download.save_as(str(destination))
    return destination
