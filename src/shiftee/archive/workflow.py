"""전체 워크플로우 통합 모듈."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from .attendance import download_payroll_current_month, download_report_current_month
from .data_mapper import find_latest_shiftee_files
from .login import launch_browser, login
from .report_generator import generate_report
from .settings import ShifteeSettings

logger = logging.getLogger(__name__)


class WorkflowConfig:
    """워크플로우 설정 클래스."""

    def __init__(
        self,
        template_path: Path | str | None = None,
        output_path: Path | str | None = None,
        data_dir: Path | str | None = None,
        skip_download: bool = False,
        validate: bool = True,
        overwrite: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ):
        """워크플로우 설정 초기화.

        Args:
            template_path: 템플릿 Excel 파일 경로
            output_path: 출력 파일 경로
            data_dir: 다운로드 데이터 디렉터리
            skip_download: 다운로드 단계 건너뛰기
            validate: 검증 수행 여부
            overwrite: 기존 파일 덮어쓰기 여부
        """
        self.template_path = Path(template_path) if template_path else None
        self.output_path = Path(output_path) if output_path else None
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.skip_download = skip_download
        self.validate = validate
        self.overwrite = overwrite
        self.start_date = start_date
        self.end_date = end_date


class ShifteeWorkflow:
    """Shiftee 자동화 워크플로우 클래스."""

    def __init__(
        self,
        settings: ShifteeSettings | None = None,
        config: WorkflowConfig | None = None,
    ):
        """워크플로우 초기화.

        Args:
            settings: Shiftee 설정
            config: 워크플로우 설정
        """
        self.settings = settings or ShifteeSettings()
        self.config = config or WorkflowConfig()

    async def download_data(self) -> dict[str, Path]:
        """Shiftee에서 데이터 다운로드.

        Returns:
            다운로드된 파일 경로 딕셔너리
        """
        logger.info("=" * 60)
        logger.info("1단계: Shiftee 데이터 다운로드")
        logger.info("=" * 60)

        async with launch_browser(self.settings) as (_, _, page):
            # 로그인
            logger.info("Shiftee 로그인 중...")
            await login(page, self.settings)
            logger.info("✅ 로그인 성공")

            # REALTIME-REPORT 다운로드
            logger.info("REALTIME-REPORT 다운로드 중...")
            report_path = await download_report_current_month(
                page, 
                self.settings, 
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            logger.info(f"✅ REALTIME-REPORT 다운로드 완료: {report_path}")

            # PAYROLL 다운로드
            logger.info("PAYROLL 다운로드 중...")
            payroll_path = await download_payroll_current_month(
                page, 
                self.settings,
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            logger.info(f"✅ PAYROLL 다운로드 완료: {payroll_path}")

        return {"realtime": report_path, "payroll": payroll_path}

    def generate_report_from_files(
        self,
        realtime_path: Path | str,
        payroll_path: Path | str,
    ) -> dict[str, Any]:
        """파일에서 보고서 생성.

        Args:
            realtime_path: REALTIME-REPORT 파일 경로
            payroll_path: PAYROLL 파일 경로

        Returns:
            생성 결과 딕셔너리
        """
        logger.info("=" * 60)
        logger.info("2단계: Excel 보고서 생성")
        logger.info("=" * 60)

        # 템플릿 경로 확인
        if not self.config.template_path:
            raise ValueError("템플릿 파일 경로가 지정되지 않았습니다")

        if not self.config.template_path.exists():
            raise FileNotFoundError(
                f"템플릿 파일을 찾을 수 없습니다: {self.config.template_path}"
            )

        # 출력 경로 설정
        output_path = self.config.output_path
        if not output_path:
            # 기본 출력 경로: output/report_YYYYMMDD.xlsx
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("output") / f"report_{timestamp}.xlsx"

        # 출력 디렉터리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"템플릿: {self.config.template_path}")
        logger.info(f"REALTIME: {realtime_path}")
        logger.info(f"PAYROLL: {payroll_path}")
        logger.info(f"출력: {output_path}")

        # 보고서 생성
        result = generate_report(
            template_path=self.config.template_path,
            realtime_report_path=realtime_path,
            payroll_path=payroll_path,
            output_path=output_path,
            overwrite=self.config.overwrite,
            validate=self.config.validate,
        )

        if result["success"]:
            logger.info("=" * 60)
            logger.info("✅ 보고서 생성 완료")
            logger.info("=" * 60)
            logger.info(f"출력 파일: {result['output_path']}")

            # 경고 출력
            if result.get("warnings"):
                logger.warning("⚠️  경고 사항:")
                for warning in result["warnings"]:
                    logger.warning(f"  - {warning}")

            # 검증 결과 출력
            if self.config.validate and result.get("validation_checks"):
                validation = result["validation_checks"]
                if validation["all_valid"]:
                    logger.info("✅ 모든 검증 통과")
                else:
                    logger.error("❌ 검증 실패:")
                    for error in validation.get("errors", []):
                        logger.error(f"  - {error}")
        else:
            logger.error("=" * 60)
            logger.error("❌ 보고서 생성 실패")
            logger.error("=" * 60)
            for error in result.get("errors", []):
                logger.error(f"  - {error}")

        return result

    async def run_full_workflow(self) -> dict[str, Any]:
        """전체 워크플로우 실행.

        Returns:
            워크플로우 실행 결과
        """
        result = {
            "success": False,
            "download": None,
            "generate": None,
            "errors": [],
        }

        try:
            # 1단계: 데이터 다운로드 (건너뛰기 옵션 확인)
            if self.config.skip_download:
                logger.info("다운로드 단계 건너뛰기 (--skip-download 옵션)")
                logger.info("data 디렉터리에서 최신 파일 검색 중...")

                # 최신 파일 찾기
                latest_files = find_latest_shiftee_files(self.config.data_dir)

                if not latest_files["realtime"]:
                    raise FileNotFoundError(
                        f"REALTIME-REPORT 파일을 찾을 수 없습니다: {self.config.data_dir}"
                    )
                if not latest_files["payroll"]:
                    raise FileNotFoundError(
                        f"PAYROLL 파일을 찾을 수 없습니다: {self.config.data_dir}"
                    )

                download_result = latest_files
                logger.info(f"✅ REALTIME: {download_result['realtime']}")
                logger.info(f"✅ PAYROLL: {download_result['payroll']}")
            else:
                download_result = await self.download_data()

            result["download"] = download_result

            # 2단계: 보고서 생성
            generate_result = self.generate_report_from_files(
                realtime_path=download_result["realtime"],
                payroll_path=download_result["payroll"],
            )
            result["generate"] = generate_result

            # 전체 성공 여부
            result["success"] = generate_result["success"]

        except Exception as e:
            result["errors"].append(f"워크플로우 실행 실패: {e}")
            logger.error(f"워크플로우 실행 실패: {e}", exc_info=True)

        return result


async def run_workflow(
    settings: ShifteeSettings | None = None,
    config: WorkflowConfig | None = None,
) -> dict[str, Any]:
    """워크플로우 실행 (헬퍼 함수).

    Args:
        settings: Shiftee 설정
        config: 워크플로우 설정

    Returns:
        워크플로우 실행 결과
    """
    workflow = ShifteeWorkflow(settings=settings, config=config)
    return await workflow.run_full_workflow()
