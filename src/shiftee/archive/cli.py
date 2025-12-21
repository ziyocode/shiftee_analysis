"""CLI 명령줄 인터페이스 모듈."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from .calculator import ShifteeCalculator
from .data_mapper import find_latest_shiftee_files
from .report_generator import generate_report
from .risk_analysis import RiskAnalyzer
from .settings import ShifteeSettings
from .validator import validate_report
from .workflow import ShifteeWorkflow, WorkflowConfig


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """로깅 설정.

    Args:
        verbose: 상세 로깅 (DEBUG)
        quiet: 최소 로깅 (WARNING)
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """CLI 파서 생성.

    Returns:
        ArgumentParser 인스턴스
    """
    parser = argparse.ArgumentParser(
        description="Shiftee 급여 보고서 자동화 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 전체 워크플로우 실행 (다운로드 + 보고서 생성)
  python shiftee_analysis.py full --template template.xlsx

  # 다운로드만 수행
  python shiftee_analysis.py download

  # 이미 다운로드된 파일로 보고서 생성
  python shiftee_analysis.py generate --template template.xlsx --skip-download

  # 생성된 보고서 검증
  python shiftee_analysis.py validate output/report.xlsx

  # 위험 직군 분석
  python shiftee_analysis.py analyze-risk
        """,
    )

    # 공통 옵션
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세 로깅 활성화",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="최소 로깅 (경고만 표시)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="설정 파일 경로 (기본: .env)",
    )

    # 서브 커맨드
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # full: 전체 워크플로우
    full_parser = subparsers.add_parser(
        "full",
        help="전체 워크플로우 실행 (다운로드 + 보고서 생성)",
    )
    full_parser.add_argument(
        "--template",
        type=Path,
        required=True,
        help="템플릿 Excel 파일 경로",
    )
    full_parser.add_argument(
        "--output",
        type=Path,
        help="출력 파일 경로 (기본: output/report_YYYYMMDD.xlsx)",
    )
    full_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="다운로드 데이터 디렉터리 (기본: data)",
    )
    full_parser.add_argument(
        "--skip-download",
        action="store_true",
        help="다운로드 건너뛰기 (기존 파일 사용)",
    )
    full_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="기존 출력 파일 덮어쓰기",
    )
    full_parser.add_argument(
        "--no-validate",
        action="store_true",
        help="검증 단계 건너뛰기",
    )
    full_parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="브라우저 헤드리스 모드 (기본값)",
    )
    full_parser.add_argument(
        "--no-headless",
        action="store_true",
        help="브라우저 표시 (디버깅용)",
    )
    full_parser.add_argument(
        "--start",
        help="시작 날짜 (YYYY.MM.DD)",
    )
    full_parser.add_argument(
        "--end",
        help="종료 날짜 (YYYY.MM.DD)",
    )

    # download: 다운로드만
    download_parser = subparsers.add_parser(
        "download",
        help="Shiftee에서 데이터 다운로드만 수행",
    )
    download_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="다운로드 데이터 디렉터리 (기본: data)",
    )
    download_parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="브라우저 헤드리스 모드 (기본값)",
    )
    download_parser.add_argument(
        "--no-headless",
        action="store_true",
        help="브라우저 표시 (디버깅용)",
    )
    download_parser.add_argument(
        "--start",
        help="시작 날짜 (YYYY.MM.DD)",
    )
    download_parser.add_argument(
        "--end",
        help="종료 날짜 (YYYY.MM.DD)",
    )

    # generate: 보고서 생성만
    generate_parser = subparsers.add_parser(
        "generate",
        help="다운로드된 파일로 보고서 생성",
    )
    generate_parser.add_argument(
        "--template",
        type=Path,
        required=True,
        help="템플릿 Excel 파일 경로",
    )
    generate_parser.add_argument(
        "--realtime",
        type=Path,
        help="REALTIME-REPORT 파일 경로 (자동 검색 시 생략 가능)",
    )
    generate_parser.add_argument(
        "--payroll",
        type=Path,
        help="PAYROLL 파일 경로 (자동 검색 시 생략 가능)",
    )
    generate_parser.add_argument(
        "--output",
        type=Path,
        help="출력 파일 경로 (기본: output/report_YYYYMMDD.xlsx)",
    )
    generate_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="데이터 디렉터리 (자동 검색 시 사용, 기본: data)",
    )
    generate_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="기존 출력 파일 덮어쓰기",
    )
    generate_parser.add_argument(
        "--no-validate",
        action="store_true",
        help="검증 단계 건너뛰기",
    )

    # validate: 검증만
    validate_parser = subparsers.add_parser(
        "validate",
        help="생성된 보고서 검증",
    )
    validate_parser.add_argument(
        "report",
        type=Path,
        help="검증할 보고서 파일 경로",
    )
    validate_parser.add_argument(
        "--validate-notice",
        action="store_true",
        help="공지용 시트도 검증 (기본: 건너뛰기)",
    )

    # analyze-risk: 위험 분석
    risk_parser = subparsers.add_parser(
        "analyze-risk",
        help="초과근로 위험 직원 분석",
    )
    risk_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="데이터 디렉터리 (기본: data)",
    )
    risk_parser.add_argument(
        "--output",
        type=Path,
        help="결과 파일 경로 (JSON/Excel). 미지정 시 콘솔 출력",
    )



    # calculate-sheet: 계산 시트 재현
    calc_parser = subparsers.add_parser(
        "calculate-sheet",
        help="계산 시트 로직 재현 및 결과 저장",
    )
    calc_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="데이터 디렉터리 (기본: data)",
    )
    calc_parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/calculation_result.xlsx"),
        help="결과 저장 경로 (기본: output/calculation_result.xlsx)",
    )

    return parser


async def cmd_full(args: argparse.Namespace) -> int:
    """전체 워크플로우 실행.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    # 설정 로드
    settings = ShifteeSettings()
    if args.no_headless:
        settings.headless = False

    # 워크플로우 설정
    config = WorkflowConfig(
        template_path=args.template,
        output_path=args.output,
        data_dir=args.data_dir,
        skip_download=args.skip_download,
        validate=not args.no_validate,
        overwrite=args.overwrite,
        start_date=args.start,
        end_date=args.end,
    )

    # 워크플로우 실행
    workflow = ShifteeWorkflow(settings=settings, config=config)
    result = await workflow.run_full_workflow()

    return 0 if result["success"] else 1


async def cmd_download(args: argparse.Namespace) -> int:
    """다운로드만 수행.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    # 설정 로드
    settings = ShifteeSettings()
    if args.no_headless:
        settings.headless = False

    # 워크플로우 설정
    config = WorkflowConfig(
        data_dir=args.data_dir,
        skip_download=False,
        start_date=args.start,
        end_date=args.end,
    )

    # 다운로드만 수행
    workflow = ShifteeWorkflow(settings=settings, config=config)
    try:
        result = await workflow.download_data()
        logging.info("=" * 60)
        logging.info("✅ 다운로드 완료")
        logging.info("=" * 60)
        logging.info(f"REALTIME: {result['realtime']}")
        logging.info(f"PAYROLL: {result['payroll']}")
        return 0
    except Exception as e:
        logging.error(f"❌ 다운로드 실패: {e}", exc_info=True)
        return 1


def cmd_generate(args: argparse.Namespace) -> int:
    """보고서 생성만 수행.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    # 파일 경로 결정
    if args.realtime and args.payroll:
        realtime_path = args.realtime
        payroll_path = args.payroll
    else:
        # 자동 검색
        logging.info(f"데이터 디렉터리에서 최신 파일 검색 중: {args.data_dir}")
        latest_files = find_latest_shiftee_files(args.data_dir)

        if not latest_files["realtime"]:
            logging.error(
                f"REALTIME-REPORT 파일을 찾을 수 없습니다: {args.data_dir}"
            )
            return 1
        if not latest_files["payroll"]:
            logging.error(f"PAYROLL 파일을 찾을 수 없습니다: {args.data_dir}")
            return 1

        realtime_path = latest_files["realtime"]
        payroll_path = latest_files["payroll"]

    # 출력 경로 설정
    output_path = args.output
    if not output_path:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("output") / f"report_{timestamp}.xlsx"

    # 출력 디렉터리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 보고서 생성
    logging.info("=" * 60)
    logging.info("보고서 생성")
    logging.info("=" * 60)
    logging.info(f"템플릿: {args.template}")
    logging.info(f"REALTIME: {realtime_path}")
    logging.info(f"PAYROLL: {payroll_path}")
    logging.info(f"출력: {output_path}")

    result = generate_report(
        template_path=args.template,
        realtime_report_path=realtime_path,
        payroll_path=payroll_path,
        output_path=output_path,
        overwrite=args.overwrite,
        validate=not args.no_validate,
    )

    if result["success"]:
        logging.info("=" * 60)
        logging.info("✅ 보고서 생성 완료")
        logging.info("=" * 60)
        logging.info(f"출력 파일: {result['output_path']}")

        # 경고 출력
        if result.get("warnings"):
            logging.warning("⚠️  경고 사항:")
            for warning in result["warnings"]:
                logging.warning(f"  - {warning}")

        return 0
    else:
        logging.error("=" * 60)
        logging.error("❌ 보고서 생성 실패")
        logging.error("=" * 60)
        for error in result.get("errors", []):
            logging.error(f"  - {error}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """보고서 검증.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    logging.info("=" * 60)
    logging.info(f"보고서 검증: {args.report}")
    logging.info("=" * 60)

    result = validate_report(args.report)

    if result["all_valid"]:
        logging.info("=" * 60)
        logging.info("✅ 모든 검증 통과")
        logging.info("=" * 60)

        # 상세 정보
        if result.get("data_sheets"):
            logging.info("데이터 시트:")
            for sheet, count in result["data_sheets"]["row_counts"].items():
                logging.info(f"  - {sheet}: {count}행")

        if result.get("calculation_sheets"):
            logging.info("계산 시트:")
            for sheet, count in result["calculation_sheets"]["formula_count"].items():
                logging.info(f"  - {sheet}: {count}개 수식")

        return 0
    else:
        logging.error("=" * 60)
        logging.error("❌ 검증 실패")
        logging.error("=" * 60)
        for error in result.get("errors", []):
            logging.error(f"  - {error}")
        return 1


def cmd_analyze_risk(args: argparse.Namespace) -> int:
    """위험 직군 분석.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드
    """
    logging.info("=" * 60)
    logging.info("초과근로 위험 분석")
    logging.info("=" * 60)

    # 파일 검색
    files = find_latest_shiftee_files(args.data_dir)
    realtime_path = files["realtime"]
    payroll_path = files["payroll"]

    if not realtime_path or not payroll_path:
        logging.error("데이터 파일을 찾을 수 없습니다. 먼저 'download' 명령을 실행하세요.")
        return 1
    
    logging.info(f"REALTIME: {realtime_path}")
    logging.info(f"PAYROLL: {payroll_path}")

    try:
        analyzer = RiskAnalyzer(realtime_path, payroll_path)
        results = analyzer.analyze()
        
        # Filter dangerous users
        risk_users = [r for r in results if r.is_risk or r.status != "정상"]
        
        logging.info("-" * 60)
        logging.info(f"분석 완료: 총 {len(results)}명 중 {len(risk_users)}명 위험")
        logging.info("-" * 60)
        
        if not risk_users:
            logging.info("✅ 위험 대상자가 없습니다.")
        else:
            for user in risk_users:
                logging.warning(
                    f"[{user.status}] {user.name} ({user.dept}): "
                    f"초과 {user.overtime_hours:.1f}h (한도 {user.limit_hours:.1f}h)"
                )
        
        # Save output if requested
        if args.output:
            import json
            out_path = args.output
            data = [r.model_dump() for r in risk_users]
            
            if out_path.suffix == '.json':
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif out_path.suffix == '.xlsx':
                pd.DataFrame([r.model_dump() for r in results]).to_excel(out_path, index=False)
                
            logging.info(f"결과 저장 완료: {out_path}")

        return 0

    except Exception as e:
        logging.error(f"❌ 분석 실패: {e}", exc_info=True)
        return 1


def cmd_calculate_sheet(args: argparse.Namespace) -> int:
    """계산 시트 재현 및 저장.

    Args:
        args: 명령줄 인자

    Returns:
        종료 코드
    """
    logging.info("=" * 60)
    logging.info("계산 시트 로직 재현")
    logging.info("=" * 60)

    files = find_latest_shiftee_files(args.data_dir)
    realtime_path = files["realtime"]
    payroll_path = files["payroll"]

    if not realtime_path or not payroll_path:
        logging.error("데이터 파일을 찾을 수 없습니다. 먼저 'download' 명령을 실행하세요.")
        return 1
    
    logging.info(f"REALTIME: {realtime_path}")
    logging.info(f"PAYROLL: {payroll_path}")

    try:
        # Load Data
        df_real = pd.read_excel(realtime_path)
        
        # Get date range from Payroll header
        df_pay_header = pd.read_excel(payroll_path, header=None, nrows=3)
        date_range_str = str(df_pay_header.iloc[1, 0])
        logging.info(f"기간: {date_range_str}")
        
        # Load Payroll Body
        df_pay = pd.read_excel(payroll_path, header=2)
        df_pay = df_pay[df_pay['이름'].notna()].copy()

        # Calculate
        calculator = ShifteeCalculator(df_real, df_pay)
        result_df = calculator.calculate_all(limit_date_str=date_range_str)
        
        # Save
        output_path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_excel(output_path, index=False)
        
        logging.info("-" * 60)
        logging.info("✅ 계산 완료 및 저장 성공")
        logging.info(f"파일 경로: {output_path}")
        
        # Show sample
        sample_risk = result_df[result_df['적정성'] == '위험']
        if not sample_risk.empty:
            logging.warning(f"위험 대상자 {len(sample_risk)}명 발견")
            
        return 0

    except Exception as e:
        logging.error(f"❌ 계산 실패: {e}", exc_info=True)
        return 1


async def async_main(argv: list[str] | None = None) -> int:
    """비동기 메인 함수.

    Args:
        argv: 명령줄 인자 리스트

    Returns:
        종료 코드
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # 로깅 설정
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # 명령어 실행
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "full":
        return await cmd_full(args)
    elif args.command == "download":
        return await cmd_download(args)
    elif args.command == "generate":
        return cmd_generate(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "analyze-risk":
        return cmd_analyze_risk(args)
    elif args.command == "calculate-sheet":
        return cmd_calculate_sheet(args)
    else:
        parser.print_help()
        return 1


def main(argv: list[str] | None = None) -> int:
    """CLI 메인 진입점.

    Args:
        argv: 명령줄 인자 리스트

    Returns:
        종료 코드
    """
    try:
        return asyncio.run(async_main(argv))
    except KeyboardInterrupt:
        logging.info("\n프로그램이 사용자에 의해 중단되었습니다.")
        return 130
    except Exception as e:
        logging.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
