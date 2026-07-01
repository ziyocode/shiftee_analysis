"""Download attendance reports."""

import logging
import re
from datetime import date, datetime
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .settings import ShifteeSettings


async def _save_failure_artifacts(page: Page, label: str) -> None:
    """실패 시 스크린샷+HTML을 logs/screenshots에 저장한다.

    원격 .exe 사용자가 원인을 보내올 수 있도록 debug 설정과 무관하게 항상 남긴다.
    아티팩트 저장 자체가 실패해도 원래 예외를 가리지 않도록 모두 무시한다.
    """
    logger = logging.getLogger("shiftee")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = Path("logs/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=f"logs/screenshots/{timestamp}_ERROR_{label}.png")
        html_content = await page.content()
        with open(f"logs/screenshots/{timestamp}_ERROR_{label}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.debug(f"Error artifacts saved: {timestamp}_ERROR_{label}.png/.html")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to save error artifacts (ignored)")


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
            # 신규 /app SPA는 로그인 직후 networkidle가 떠도 사이드바(nav)를 클라이언트에서
            # 뒤늦게 렌더한다. nav가 그려지기 전에 즉시 조회하면 0건이 되어, 이전에는
            # 'text=리포트' 폴백이 타임아웃으로 실패했다(v1.0.1 Windows 증상).
            # 먼저 매니저 nav 링크가 DOM에 붙을 때까지 기다려 레이스를 제거한다.
            logger.debug("Waiting for SPA navigation to render after login")
            nav_link = page.locator("a[href*='/manager/']").first
            try:
                await nav_link.wait_for(state="attached", timeout=max(settings.timeout, 90000))
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(
                    "로그인 후 메뉴(사이드바)가 렌더되지 않았습니다. 로그인 성공 여부와 "
                    "네트워크 상태를 확인하세요(신규 /app 화면 로딩 실패 가능)."
                ) from exc

            if settings.debug_screenshots:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"logs/screenshots/{timestamp}_report_01_before_link_click.png")
                logger.debug(f"Screenshot saved: {timestamp}_report_01_before_link_click.png")

            # 리포트 URL 확보: 1) 리포트 링크의 href, 2) 현재 URL/다른 nav 링크의 회사 ID로 구성.
            # 링크 텍스트 매칭에 의존하지 않아 사이드바 접힘/렌더 상태와 무관하게 동작한다.
            logger.debug("Resolving report page URL")
            report_link = page.locator("a[href*='/manager/report']").first
            href = await report_link.get_attribute("href") if await report_link.count() else None
            if not href:
                match = re.search(r"/companies/(\d+)/", page.url)
                if not match:
                    nav_href = await nav_link.get_attribute("href") or ""
                    match = re.search(r"/companies/(\d+)/", nav_href)
                if match:
                    href = f"/app/companies/{match.group(1)}/manager/report"
            if not href:
                raise RuntimeError(
                    "리포트 페이지 URL을 찾지 못했습니다(사이드바에 '리포트' 메뉴 없음). "
                    "계정 권한을 확인하세요."
                )
            report_url = href if href.startswith("http") else f"https://shiftee.io{href}"
            logger.debug(f"Navigating to report URL: {report_url}")
            await page.goto(report_url, wait_until="domcontentloaded")
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
        # 실패 원인 분석을 위해 항상 스크린샷/HTML을 남긴다(.exe 배포 원격 디버깅용).
        await _save_failure_artifacts(page, "report")
        raise


async def download_leave_accrual_current(
    page: Page,
    settings: ShifteeSettings,
    output_dir: Path | None = None,
) -> Path:
    """
    From the left nav, open 휴가 -> 휴가 발생 -> 다운로드 -> 휴가 발생 -> 다운로드 and save the file.

    기간(조회 기간)은 건드리지 않는다. 모달 기본값은 '올해 1.1 ~ 12.31'인데,
    대체휴가 등 발생분은 만료 시점까지 몇 개월 내로 짧게 순환돼 실사용 데이터에서
    작년 이전 발생 중 '발생됨(미만료)' 건이 없음을 확인했다 (전체 기간 다운로드와 비교 검증).
    """
    logger = logging.getLogger("shiftee")
    logger.info("Starting leave accrual download")

    output_dir = output_dir or Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if settings.leave_accrual_url:
            nav_url = settings.leave_accrual_url
        else:
            leave_link = page.locator("a[href*='/manager/leave-accruals']").first
            href = await leave_link.get_attribute("href")
            nav_url = href if href and href.startswith("http") else f"https://shiftee.io{href}"
        logger.debug(f"Navigating to leave accrual URL: {nav_url}")
        await page.goto(nav_url, wait_until="domcontentloaded")

        logger.debug("Waiting for page to be fully loaded")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        logger.debug("Page fully loaded")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_leave_01_page_loaded.png")
            logger.debug(f"Screenshot saved: {timestamp}_leave_01_page_loaded.png")

        logger.debug("Waiting for download toggle button to be visible")
        toggle = page.locator('button:has-text("다운로드")').first
        await toggle.wait_for(state="visible", timeout=settings.timeout)
        await toggle.click()
        await page.wait_for_timeout(200)

        logger.debug("Clicking '휴가 발생' 다운로드 menu item")
        # 사이드바에도 같은 텍스트의 링크(휴가 발생 설정 페이지)가 있어 드롭다운 컨테이너로 한정한다.
        leave_item = page.locator(".sft-dropdown-container li.dropdown-item", has_text="휴가 발생").first
        await leave_item.click(force=True)

        logger.debug("Waiting for network idle after menu item click")
        await page.wait_for_load_state("networkidle", timeout=settings.timeout)
        await page.wait_for_timeout(1000)

        logger.debug("Waiting for export modal to be attached to DOM")
        modal = page.locator("sft-basic-export-modal").first
        await modal.wait_for(state="attached", timeout=settings.timeout)
        await modal.wait_for(state="visible", timeout=settings.timeout)
        logger.debug("Leave accrual modal visible")

        if settings.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/{timestamp}_leave_02_modal_visible.png")
            logger.debug(f"Screenshot saved: {timestamp}_leave_02_modal_visible.png")

        logger.debug("Clicking final download button in modal")
        confirm_download = modal.locator('button:has-text("다운로드")').last
        try:
            async with page.expect_download(timeout=max(settings.timeout, 120000)) as dl_info:
                await confirm_download.click(force=True)
            download = await dl_info.value
            logger.debug("Download started successfully")
        except PlaywrightTimeoutError as exc:
            timeout_seconds = settings.timeout / 1000
            logger.error(f"Download timeout after {timeout_seconds}s")
            raise RuntimeError(
                f"Download did not start within {timeout_seconds}s after confirming in the 휴가 발생 popup. "
                "Check that the modal rendered correctly and that the account has export permissions."
            ) from exc

        filename = "shiftee_leave.xlsx"
        destination = output_dir / filename
        await download.save_as(str(destination))
        logger.info(f"Leave accrual saved to: {destination}")
        return destination

    except Exception as e:
        logger.error(f"Leave accrual download failed: {type(e).__name__}: {e}")
        await _save_failure_artifacts(page, "leave")
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

        # 직원들: 드롭다운을 열어 전체 선택.
        # 주의: '모두 선택'은 토글이며, 신규 /app SPA에서는 모달 진입 시 직원이 이미
        # 전체 선택돼 있다(예: "280 선택됨"). 무조건 한 번만 클릭하면 전체가 '해제'되어
        # 직원 0명 → 폼이 ng-invalid → 다운로드 버튼이 비활성인 채로 멈춘다.
        # 클릭 후 라벨이 '선택안됨'이면 다시 눌러 전체 선택 상태를 보장한다.
        logger.debug("Selecting all employees")
        employee_dropdown = modal.locator("sft-multi-select-employees .dropdown-toggle").first
        await employee_dropdown.click()
        select_all = modal.locator("sft-multi-select-employees .sft-dropdown-item-select-all").first
        await select_all.wait_for(state="visible", timeout=settings.timeout)
        await page.wait_for_timeout(300)  # 가상 스크롤 목록 렌더 안정화
        employee_label = modal.locator("sft-multi-select-employees .sft-btn-name").first
        await select_all.click()
        await page.wait_for_timeout(400)
        if (await employee_label.inner_text()).strip() == "선택안됨":
            logger.debug("Select-all toggled off; clicking again to select all employees")
            await select_all.click()
            await page.wait_for_timeout(400)
        logger.debug(f"Employees selected: {(await employee_label.inner_text()).strip()}")
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
        # 실패 원인 분석을 위해 항상 스크린샷/HTML을 남긴다(.exe 배포 원격 디버깅용).
        await _save_failure_artifacts(page, "payroll")
        raise
