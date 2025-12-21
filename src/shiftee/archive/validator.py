"""보고서 검증 모듈."""

import logging
from pathlib import Path
from typing import Any

from .excel_processor import ExcelProcessor
from .template import TemplateManager

logger = logging.getLogger(__name__)


class ReportValidator:
    """보고서 검증 클래스."""

    # 검증할 시트별 최소 데이터 행 수
    MIN_DATA_ROWS = {
        "shiftee데이타": 1,  # 최소 1명의 직원 데이터
        "shiftee데이타2": 1,  # 최소 1명의 직원 데이터
    }

    # 공지용 시트의 필수 컬럼 (예시)
    NOTICE_REQUIRED_COLUMNS = [
        "직원",
        "사원번호",
    ]

    def __init__(self, report_path: Path | str):
        """검증기 초기화.

        Args:
            report_path: 검증할 보고서 파일 경로

        Raises:
            FileNotFoundError: 파일을 찾을 수 없을 때
        """
        self.report_path = Path(report_path)
        if not self.report_path.exists():
            raise FileNotFoundError(f"보고서 파일을 찾을 수 없습니다: {self.report_path}")

        self.processor = ExcelProcessor(self.report_path)

    def validate_sheet_structure(self) -> dict[str, Any]:
        """시트 구조 검증.

        Returns:
            검증 결과 딕셔너리
        """
        result = {
            "valid": True,
            "missing_sheets": [],
            "errors": [],
        }

        sheet_names = set(self.processor.get_sheet_names())

        # 필수 시트 확인
        missing_sheets = TemplateManager.REQUIRED_SHEETS - sheet_names
        if missing_sheets:
            result["valid"] = False
            result["missing_sheets"] = list(missing_sheets)
            result["errors"].append(f"필수 시트가 없습니다: {missing_sheets}")
            logger.error(f"필수 시트 누락: {missing_sheets}")

        return result

    def validate_data_sheets(self) -> dict[str, Any]:
        """데이터 시트 검증.

        Returns:
            검증 결과 딕셔너리
        """
        result = {
            "valid": True,
            "empty_sheets": [],
            "row_counts": {},
            "errors": [],
        }

        for sheet_name, min_rows in self.MIN_DATA_ROWS.items():
            try:
                sheet = self.processor.get_sheet(sheet_name)

                # 데이터 행 수 계산
                if sheet_name == "shiftee데이타":
                    # 2번째 행부터 데이터
                    data_start_row = 2
                elif sheet_name == "shiftee데이타2":
                    # 4번째 행부터 데이터
                    data_start_row = 4
                else:
                    data_start_row = 2

                # 실제 데이터가 있는 행 수 계산
                data_row_count = 0
                for row_idx in range(data_start_row, sheet.max_row + 1):
                    # 첫 번째 셀에 데이터가 있는지 확인
                    cell_value = sheet.cell(row=row_idx, column=1).value
                    if cell_value is not None and str(cell_value).strip():
                        data_row_count += 1

                result["row_counts"][sheet_name] = data_row_count

                if data_row_count < min_rows:
                    result["valid"] = False
                    result["empty_sheets"].append(sheet_name)
                    result["errors"].append(
                        f"시트 '{sheet_name}'에 데이터가 부족합니다 "
                        f"(최소 {min_rows}행 필요, 실제 {data_row_count}행)"
                    )
                    logger.warning(
                        f"시트 '{sheet_name}' 데이터 부족: {data_row_count}행"
                    )
                else:
                    logger.info(f"시트 '{sheet_name}' 검증 통과: {data_row_count}행")

            except Exception as e:
                result["valid"] = False
                result["errors"].append(f"시트 '{sheet_name}' 검증 실패: {e}")
                logger.error(f"시트 '{sheet_name}' 검증 실패: {e}")

        return result

    def validate_calculation_sheets(self) -> dict[str, Any]:
        """계산 시트 검증.

        Returns:
            검증 결과 딕셔너리
        """
        result = {
            "valid": True,
            "formula_count": {},
            "errors": [],
        }

        calculation_sheets = ["계산", "정리"]

        for sheet_name in calculation_sheets:
            try:
                sheet = self.processor.get_sheet(sheet_name)
                formula_count = 0

                # 수식이 포함된 셀 개수 확인
                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value and str(cell.value).startswith("="):
                            formula_count += 1

                result["formula_count"][sheet_name] = formula_count

                if formula_count == 0:
                    result["valid"] = False
                    result["errors"].append(f"시트 '{sheet_name}'에 수식이 없습니다")
                    logger.warning(f"시트 '{sheet_name}'에 수식이 없습니다")
                else:
                    logger.info(f"시트 '{sheet_name}' 수식 개수: {formula_count}")

            except Exception as e:
                result["valid"] = False
                result["errors"].append(f"시트 '{sheet_name}' 검증 실패: {e}")
                logger.error(f"시트 '{sheet_name}' 검증 실패: {e}")

        return result

    def validate_notice_sheet(self) -> dict[str, Any]:
        """공지용 시트 검증.

        Returns:
            검증 결과 딕셔너리
        """
        result = {
            "valid": True,
            "has_data": False,
            "has_formulas": False,
            "row_count": 0,
            "formula_count": 0,
            "errors": [],
        }

        try:
            sheet = self.processor.get_sheet("공지용")

            # 데이터 행 수 계산 (헤더 제외)
            data_row_count = 0
            formula_count = 0
            for row_idx in range(2, sheet.max_row + 1):
                # 첫 번째 셀에 데이터나 수식이 있는지 확인
                cell = sheet.cell(row=row_idx, column=1)
                cell_value = cell.value

                # 수식이 있는 경우
                if cell_value and str(cell_value).startswith("="):
                    formula_count += 1
                # 데이터가 있는 경우
                elif cell_value is not None and str(cell_value).strip():
                    data_row_count += 1

            result["row_count"] = data_row_count
            result["formula_count"] = formula_count
            result["has_data"] = data_row_count > 0
            result["has_formulas"] = formula_count > 0

            # 데이터나 수식이 있으면 통과
            if not result["has_data"] and not result["has_formulas"]:
                result["valid"] = False
                result["errors"].append("공지용 시트에 데이터나 수식이 없습니다")
                logger.warning("공지용 시트에 데이터나 수식이 없습니다")
            elif result["has_formulas"] and not result["has_data"]:
                # 수식만 있고 데이터가 없는 경우 (Excel에서 열면 계산될 예정)
                logger.info(f"공지용 시트에 {formula_count}개 수식 존재 (Excel에서 열면 계산됨)")
            else:
                logger.info(f"공지용 시트 데이터 행 수: {data_row_count}")

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"공지용 시트 검증 실패: {e}")
            logger.error(f"공지용 시트 검증 실패: {e}")

        return result

    def validate_all(self, validate_notice: bool = False) -> dict[str, Any]:
        """전체 검증 수행.

        Args:
            validate_notice: 공지용 시트 검증 여부 (기본값: False)
                            공지용 시트는 Excel에서 열어서 수동으로 처리하거나
                            VBA 매크로로 생성되므로, 기본적으로 검증하지 않음

        Returns:
            종합 검증 결과 딕셔너리
        """
        logger.info(f"보고서 검증 시작: {self.report_path}")

        result = {
            "all_valid": True,
            "structure": None,
            "data_sheets": None,
            "calculation_sheets": None,
            "notice_sheet": None,
            "errors": [],
            "warnings": [],
        }

        # 1. 시트 구조 검증
        logger.info("시트 구조 검증 중...")
        structure_result = self.validate_sheet_structure()
        result["structure"] = structure_result

        if not structure_result["valid"]:
            result["all_valid"] = False
            result["errors"].extend(structure_result.get("errors", []))

        # 2. 데이터 시트 검증
        logger.info("데이터 시트 검증 중...")
        data_result = self.validate_data_sheets()
        result["data_sheets"] = data_result

        if not data_result["valid"]:
            result["all_valid"] = False
            result["errors"].extend(data_result.get("errors", []))

        # 3. 계산 시트 검증
        logger.info("계산 시트 검증 중...")
        calc_result = self.validate_calculation_sheets()
        result["calculation_sheets"] = calc_result

        if not calc_result["valid"]:
            result["all_valid"] = False
            result["errors"].extend(calc_result.get("errors", []))

        # 4. 공지용 시트 검증 (선택적)
        if validate_notice:
            logger.info("공지용 시트 검증 중...")
            notice_result = self.validate_notice_sheet()
            result["notice_sheet"] = notice_result

            if not notice_result["valid"]:
                result["all_valid"] = False
                result["errors"].extend(notice_result.get("errors", []))
        else:
            logger.info("공지용 시트 검증 생략 (Excel에서 열어서 확인 필요)")
            result["warnings"].append("공지용 시트는 Excel에서 열어서 확인이 필요합니다")

        if result["all_valid"]:
            logger.info("✅ 모든 검증 통과")
        else:
            logger.error(f"❌ 검증 실패: {len(result['errors'])}개 오류")

        return result

    def close(self) -> None:
        """리소스 정리."""
        self.processor.close()

    def __enter__(self) -> "ReportValidator":
        """Context manager 진입."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager 종료."""
        self.close()


def validate_report(report_path: Path | str) -> dict[str, Any]:
    """보고서 검증 (헬퍼 함수).

    Args:
        report_path: 검증할 보고서 파일 경로

    Returns:
        검증 결과 딕셔너리
    """
    with ReportValidator(report_path) as validator:
        return validator.validate_all()
