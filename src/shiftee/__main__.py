"""Shiftee 모듈 직접 실행 진입점.

사용 예시:
    python -m src.shiftee full --template template.xlsx
    python -m src.shiftee download
    python -m src.shiftee generate --template template.xlsx
    python -m src.shiftee validate output/report.xlsx
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())

