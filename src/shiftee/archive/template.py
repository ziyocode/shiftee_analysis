"""템플릿 Excel 파일 관리 모듈."""

from pathlib import Path
from typing import Literal

from .excel_processor import ExcelProcessor


class TemplateManager:
    """템플릿 Excel 파일 관리 클래스."""

    # 필수 시트 이름
    REQUIRED_SHEETS = {
        "작성법",
        "shiftee데이타",
        "shiftee데이타2",
        "계산",
        "정리",
        "공지용",
    }

    # 각 시트의 예상 컬럼 수 (검증용)
    EXPECTED_COLUMNS = {
        "shiftee데이타": 25,
        "shiftee데이타2": 47,
    }

    def __init__(self, template_path: Path | str):
        """템플릿 파일 로드 및 검증.

        Args:
            template_path: 템플릿 Excel 파일 경로

        Raises:
            FileNotFoundError: 템플릿 파일이 없을 때
            ValueError: 템플릿 구조가 잘못되었을 때
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {self.template_path}")

        self.processor = ExcelProcessor(self.template_path)
        self._validate_template()

    def _validate_template(self) -> None:
        """템플릿 구조 검증.

        Raises:
            ValueError: 필수 시트가 없거나 구조가 잘못되었을 때
        """
        sheet_names = set(self.processor.get_sheet_names())

        # 필수 시트 확인
        missing_sheets = self.REQUIRED_SHEETS - sheet_names
        if missing_sheets:
            raise ValueError(
                f"템플릿에 필수 시트가 없습니다: {missing_sheets}\n"
                f"현재 시트: {sheet_names}"
            )

        # 각 시트의 기본 구조 검증
        for sheet_name, expected_cols in self.EXPECTED_COLUMNS.items():
            sheet = self.processor.get_sheet(sheet_name)

            # 첫 번째 행(헤더) 확인
            if sheet_name == "shiftee데이타":
                # shiftee데이타는 1번째 행이 헤더
                header_row = 1
            elif sheet_name == "shiftee데이타2":
                # shiftee데이타2는 2번째 행이 헤더
                header_row = 2
            else:
                continue

            # 컬럼 수 확인
            max_col = sheet.max_column
            if max_col < expected_cols:
                raise ValueError(
                    f"시트 '{sheet_name}'의 컬럼 수가 부족합니다. "
                    f"예상: {expected_cols}, 실제: {max_col}"
                )

    def create_instance(
        self, output_path: Path | str, overwrite: bool = False
    ) -> ExcelProcessor:
        """템플릿을 복사하여 새 인스턴스 생성.

        Args:
            output_path: 생성할 파일 경로
            overwrite: 기존 파일 덮어쓰기 여부

        Returns:
            새로운 ExcelProcessor 인스턴스

        Raises:
            FileExistsError: 파일이 이미 존재하고 overwrite=False일 때
        """
        output_path = Path(output_path)

        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"출력 파일이 이미 존재합니다: {output_path}\n"
                "overwrite=True로 설정하여 덮어쓰기 가능합니다."
            )

        # 템플릿 복사
        return self.processor.copy_to(output_path)

    def get_sheet_info(self, sheet_name: str) -> dict:
        """시트 정보 반환.

        Args:
            sheet_name: 시트 이름

        Returns:
            시트 정보 딕셔너리
        """
        sheet = self.processor.get_sheet(sheet_name)

        return {
            "name": sheet_name,
            "max_row": sheet.max_row,
            "max_column": sheet.max_column,
            "dimensions": sheet.dimensions,
        }

    def get_all_sheet_info(self) -> dict[str, dict]:
        """모든 시트 정보 반환.

        Returns:
            시트별 정보 딕셔너리
        """
        return {
            sheet_name: self.get_sheet_info(sheet_name)
            for sheet_name in self.processor.get_sheet_names()
        }

    def clear_data_sheets(self) -> None:
        """데이터 시트들(shiftee데이타, shiftee데이타2)의 데이터 삭제.

        헤더는 보존하고 데이터만 삭제합니다.
        """
        # shiftee데이타 삭제 (2번째 행부터)
        self.processor.clear_sheet_data("shiftee데이타", start_row=2)

        # shiftee데이타2 삭제 (4번째 행부터)
        # 1행: 메타데이터, 2행: 더미, 3행: 헤더, 4행부터: 데이터
        self.processor.clear_sheet_data("shiftee데이타2", start_row=4)

    def close(self) -> None:
        """템플릿 파일 닫기."""
        self.processor.close()

    def __enter__(self) -> "TemplateManager":
        """Context manager 진입."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager 종료."""
        self.close()


def load_template(template_path: Path | str) -> TemplateManager:
    """템플릿 로드 (헬퍼 함수).

    Args:
        template_path: 템플릿 파일 경로

    Returns:
        TemplateManager 인스턴스
    """
    return TemplateManager(template_path)


def validate_template(template_path: Path | str) -> bool:
    """템플릿 유효성 검증 (헬퍼 함수).

    Args:
        template_path: 템플릿 파일 경로

    Returns:
        검증 성공 여부
    """
    try:
        with TemplateManager(template_path):
            return True
    except (FileNotFoundError, ValueError) as e:
        print(f"템플릿 검증 실패: {e}")
        return False
