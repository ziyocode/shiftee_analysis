"""AWS Lambda 진입점.

EventBridge Scheduler에 의해 매일 실행되며, 전체 워크플로우를 오케스트레이션합니다:
1. Secrets Manager에서 자격증명 로드
2. Shiftee에서 데이터 다운로드
3. 분석 수행 및 Excel 생성
4. S3에 업로드
5. (옵션) 카카오톡 알림 전송
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import boto3

logger = logging.getLogger("shiftee-lambda")
logger.setLevel(logging.INFO)


def _load_secrets():
    """Secrets Manager에서 Shiftee 자격증명을 로드하여 환경변수로 설정."""
    client = boto3.client("secretsmanager")
    secret_name = os.environ.get("SECRET_NAME", "shiftee/credentials")

    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])

    os.environ["SHIFTEE_ID"] = secret["SHIFTEE_ID"]
    os.environ["SHIFTEE_PASSWORD"] = secret["SHIFTEE_PASSWORD"]
    logger.info("Shiftee credentials loaded from Secrets Manager")


def _upload_to_s3(local_path: Path, s3_key: str):
    """파일을 S3에 업로드."""
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        logger.warning("S3_BUCKET_NAME not set, skipping upload")
        return

    client = boto3.client("s3")
    client.upload_file(str(local_path), bucket, s3_key)
    logger.info(f"Uploaded {local_path.name} -> s3://{bucket}/{s3_key}")


async def run_workflow():
    """비동기 메인 워크플로우."""
    from .attendance import download_payroll_current_month, download_report_current_month
    from .cli import (
        calculate_basic_columns,
        calculate_g_column,
        calculate_h_column,
        calculate_i_j_l_columns,
        calculate_legal_limits_and_risk,
        calculate_overtime_columns,
        load_shiftee_data1,
        load_shiftee_data2,
        save_to_excel,
    )
    from .login import launch_browser, login
    from .settings import ShifteeSettings

    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_str = start_date.strftime("%Y.%m.%d")
    end_str = end_date.strftime("%Y.%m.%d")

    data_dir = Path("/tmp/data")
    output_dir = Path("/tmp/output")
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Shiftee 데이터 다운로드
    logger.info(f"Downloading data for {start_str} ~ {end_str}")
    settings = ShifteeSettings()

    async with launch_browser(settings) as (browser, context, page):
        await login(page, settings)
        logger.info("Login successful")

        data1_path = await download_report_current_month(
            page, settings, data_dir, start_str, end_str
        )
        logger.info(f"Report downloaded: {data1_path}")

        data2_path = await download_payroll_current_month(
            page, settings, data_dir, start_str, end_str
        )
        logger.info(f"Payroll downloaded: {data2_path}")

    # 2. 분석 수행
    logger.info("Starting analysis")
    df1 = load_shiftee_data1(data1_path)
    df2 = load_shiftee_data2(data2_path)

    # 팀 필터 (설정된 경우만 적용)
    if settings.team_filter and "본조직" in df1.columns:
        before = len(df1)
        df1 = df1[df1["본조직"] == settings.team_filter].copy()
        excluded = before - len(df1)
        if excluded:
            logger.info(f"Filtered to {settings.team_filter}: {len(df1)}명 (제외 {excluded}명)")
            if "이름" in df2.columns and "직원" in df1.columns:
                target_employees = df1["직원"].tolist()
                df2 = df2[df2["이름"].isin(target_employees)].copy()

    # 직무 제외 (설정된 경우만 적용)
    if settings.exclude_role and "본직무" in df1.columns:
        shift_workers = df1[df1["본직무"] == settings.exclude_role]["직원"].tolist() if "직원" in df1.columns else []
        df1 = df1[df1["본직무"] != settings.exclude_role].copy()
        if shift_workers:
            logger.info(f"Excluded {len(shift_workers)} {settings.exclude_role} workers")
            if "이름" in df2.columns:
                df2 = df2[~df2["이름"].isin(shift_workers)].copy()

    df = calculate_basic_columns(df1)
    df = calculate_g_column(df)
    df = calculate_h_column(df, df1, df2)
    df = calculate_i_j_l_columns(df)
    df = calculate_overtime_columns(df)
    df = calculate_legal_limits_and_risk(df, start_date, end_date)

    # 3. Excel 저장
    report_filename = f"report_{now.strftime('%Y%m%d')}.xlsx"
    report_path = output_dir / report_filename
    save_to_excel(df, report_path, start_date, end_date)
    logger.info(f"Report saved: {report_path}")

    # 4. S3 업로드
    s3_prefix = os.environ.get("S3_PREFIX", "reports")
    date_prefix = now.strftime("%Y/%m")

    _upload_to_s3(data1_path, f"{s3_prefix}/{date_prefix}/{data1_path.name}")
    _upload_to_s3(data2_path, f"{s3_prefix}/{date_prefix}/{data2_path.name}")
    _upload_to_s3(report_path, f"{s3_prefix}/{date_prefix}/{report_filename}")

    # 5. 카카오톡 알림 (옵션)
    if os.environ.get("SEND_KAKAO", "false").lower() == "true":
        try:
            from .kakao_lambda import KakaoLambda
            from kakao_send import format_risk_message

            kakao = KakaoLambda()
            message = format_risk_message(df, start_date, end_date)
            if kakao.send_message(message):
                logger.info("KakaoTalk notification sent")
            else:
                logger.warning("KakaoTalk notification failed")
        except Exception as e:
            logger.warning(f"KakaoTalk notification skipped: {e}")

    # 6. Slack 알림 (옵션)
    if os.environ.get("SEND_SLACK", "false").lower() == "true":
        try:
            from slack_send import SlackWebhook, format_slack_message

            webhook_url = settings.slack_webhook_url
            if webhook_url:
                slack = SlackWebhook(webhook_url)
                message = format_slack_message(df, start_date, end_date)
                if slack.send_message(message):
                    logger.info("Slack notification sent")
                else:
                    logger.warning("Slack notification failed")
            else:
                logger.warning("SHIFTEE_SLACK_WEBHOOK_URL not set, skipping Slack")
        except Exception as e:
            logger.warning(f"Slack notification skipped: {e}")

    # 결과 요약
    total = len(df)
    risk_count = len(df[df["U_적정성"] == "위험"])
    legal_exceed = len(df[df["V_법규기준초과자"] == "법기준초과"])

    return {
        "period": f"{start_str} ~ {end_str}",
        "total_employees": total,
        "risk_count": risk_count,
        "legal_exceed_count": legal_exceed,
        "files_uploaded": {
            "data1": data1_path.name,
            "data2": data2_path.name,
            "report": report_filename,
        },
    }


def handler(event, context):
    """Lambda 핸들러 진입점."""
    logger.info(f"Lambda invoked: {json.dumps(event)}")

    try:
        _load_secrets()
        result = asyncio.run(run_workflow())
        logger.info(f"Workflow completed: {json.dumps(result)}")
        return {"statusCode": 200, "body": json.dumps(result, ensure_ascii=False)}
    except Exception as e:
        logger.error(f"Workflow failed: {type(e).__name__}: {e}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
