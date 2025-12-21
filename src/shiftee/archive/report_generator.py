"""급여 보고서 생성 모듈."""

import logging
from pathlib import Path
from typing import Any

from .data_mapper import ShifteeDataMapper
from .excel_processor import ExcelProcessor
from .template import TemplateManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """급여 보고서 생성 클래스."""

    def __init__(
        self,
        template_path: Path | str,
        realtime_report_path: Path | str,
        payroll_path: Path | str,
    ):
        """보고서 생성기 초기화.

        Args:
            template_path: 템플릿 Excel 파일 경로
            realtime_report_path: REALTIME-REPORT 파일 경로
            payroll_path: PAYROLL 파일 경로

        Raises:
            FileNotFoundError: 필수 파일을 찾을 수 없을 때
            ValueError: 템플릿 구조가 잘못되었을 때
        """
        self.template_path = Path(template_path)
        self.realtime_report_path = Path(realtime_report_path)
        self.payroll_path = Path(payroll_path)

        # 파일 존재 확인
        self._validate_input_files()

        # 데이터 매퍼 초기화
        self.data_mapper = ShifteeDataMapper(
            realtime_report_path=self.realtime_report_path,
            payroll_path=self.payroll_path,
        )

    def _validate_input_files(self) -> None:
        """입력 파일 존재 확인.

        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {self.template_path}")

        if not self.realtime_report_path.exists():
            raise FileNotFoundError(
                f"REALTIME-REPORT 파일을 찾을 수 없습니다: {self.realtime_report_path}"
            )

        if not self.payroll_path.exists():
            raise FileNotFoundError(
                f"PAYROLL 파일을 찾을 수 없습니다: {self.payroll_path}"
            )

    def generate(
        self, output_path: Path | str, overwrite: bool = False
    ) -> dict[str, Any]:
        """보고서 생성.

        Args:
            output_path: 출력 파일 경로
            overwrite: 기존 파일 덮어쓰기 여부

        Returns:
            생성 결과 딕셔너리

        Raises:
            FileExistsError: 파일이 이미 존재하고 overwrite=False일 때
        """
        output_path = Path(output_path)
        result = {
            "success": False,
            "output_path": None,
            "validation": None,
            "errors": [],
            "warnings": [],
        }

        try:
            logger.info("보고서 생성 시작")
            logger.info(f"템플릿: {self.template_path}")
            logger.info(f"REALTIME: {self.realtime_report_path}")
            logger.info(f"PAYROLL: {self.payroll_path}")
            logger.info(f"출력: {output_path}")

            # 1. 템플릿 로드 및 검증
            logger.info("템플릿 로드 중...")
            with TemplateManager(self.template_path) as template:
                # 2. 템플릿 인스턴스 생성
                logger.info("템플릿 인스턴스 생성 중...")
                instance = template.create_instance(output_path, overwrite=overwrite)

                # 3. 데이터 매핑
                logger.info("데이터 매핑 중...")
                mapping_result = self.data_mapper.map_all_data(instance)

                # 매핑 결과 기록
                result["validation"] = mapping_result.get("validation")

                if not mapping_result["success"]:
                    result["errors"].extend(mapping_result.get("errors", []))
                    logger.error("데이터 매핑 실패")
                    return result

                # 매핑 경고 추가
                if mapping_result.get("warnings"):
                    result["warnings"].extend(mapping_result["warnings"])

                # 4. 수식 재계산을 위한 저장
                logger.info("Excel 파일 저장 중...")
                saved_path = instance.save()

                result["success"] = True
                result["output_path"] = saved_path
                logger.info(f"보고서 생성 완료: {saved_path}")

        except FileExistsError as e:
            result["errors"].append(str(e))
            logger.error(f"파일 덮어쓰기 오류: {e}")
        except Exception as e:
            result["errors"].append(f"보고서 생성 실패: {e}")
            logger.error(f"보고서 생성 실패: {e}", exc_info=True)

        return result

    def generate_with_validation(
        self, output_path: Path | str, overwrite: bool = False
    ) -> dict[str, Any]:
        """보고서 생성 및 검증.

        Args:
            output_path: 출력 파일 경로
            overwrite: 기존 파일 덮어쓰기 여부

        Returns:
            생성 및 검증 결과 딕셔너리
        """
        # 보고서 생성
        result = self.generate(output_path, overwrite=overwrite)

        if not result["success"]:
            return result

        # 검증 수행
        from .validator import ReportValidator

        validator = ReportValidator(result["output_path"])
        validation_result = validator.validate_all()

        # 검증 결과 병합
        result["validation_checks"] = validation_result
        result["validation_passed"] = validation_result["all_valid"]

        if not validation_result["all_valid"]:
            result["warnings"].extend(validation_result.get("errors", []))

        return result


def generate_report(
    template_path: Path | str,
    realtime_report_path: Path | str,
    payroll_path: Path | str,
    output_path: Path | str,
    overwrite: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """보고서 생성 (헬퍼 함수).

    Args:
        template_path: 템플릿 파일 경로
        realtime_report_path: REALTIME-REPORT 파일 경로
        payroll_path: PAYROLL 파일 경로
        output_path: 출력 파일 경로
        overwrite: 기존 파일 덮어쓰기 여부
        validate: 검증 수행 여부

    Returns:
        생성 결과 딕셔너리
    """
    generator = ReportGenerator(
        template_path=template_path,
        realtime_report_path=realtime_report_path,
        payroll_path=payroll_path,
    )

    if validate:
        return generator.generate_with_validation(output_path, overwrite=overwrite)
    else:
        return generator.generate(output_path, overwrite=overwrite)
