#!/usr/bin/env python
"""Shiftee Analysis CLI Tool.

Shiftee 데이터를 분석하여 초과근로 적정성을 판정하는 CLI 도구입니다.

Usage:
    # 기본 실행 (콘솔 출력만)
    python shiftee_analysis.py --start 2025-11-01 --end 2025-11-30

    # Excel 리포트 생성
    python shiftee_analysis.py --start 2025-11-01 --end 2025-11-30 --output report.xlsx

    # 다운로드부터 한 번에 실행
    python shiftee_analysis.py --download --start 2025-11-01 --end 2025-11-30 --output report.xlsx

    # 도움말
    python shiftee_analysis.py --help
"""

import sys
from pathlib import Path

# Add scripts directory to Python path
SCRIPTS_DIR = Path(__file__).parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import main function from calculate_risk_direct
from calculate_risk_direct import main as calculate_main


def __main__():
    """CLI 엔트리포인트."""
    try:
        sys.exit(calculate_main())
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    __main__()
