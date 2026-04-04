"""Shiftee 모듈 직접 실행 진입점.

사용 예시:
    uv run shiftee-analyze full --template template.xlsx
    uv run shiftee-analyze download
    uv run shiftee-analyze generate --template template.xlsx
    uv run shiftee-analyze validate output/report.xlsx
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
