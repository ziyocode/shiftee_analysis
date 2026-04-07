from pydantic_settings import BaseSettings, SettingsConfigDict


class ShifteeSettings(BaseSettings):
    """Configuration for Shiftee automation."""

    id: str
    password: str
    headless: bool = True
    base_url: str = "https://shiftee.io"
    calendar_url: str = "https://shiftee.io/app/companies/1920030/manager/attendances/calendar"
    report_url: str | None = None  # Optional direct URL for the Reports page
    attendance_list_url: str = "https://shiftee.io/app/companies/1920030/manager/attendances/list"

    # 분석 필터
    team_filter: str | None = None  # 특정 팀만 분석 (예: "뱅킹IS팀")
    exclude_role: str | None = "교대제"  # 제외할 직무

    # 카카오톡 알림
    kakao_app_key: str | None = None
    kakao_access_token: str | None = None
    kakao_refresh_token: str | None = None

    # Slack 알림
    slack_webhook_url: str | None = None

    # Timeout settings (milliseconds) - increased for macOS automation
    timeout: int = 60000  # Default timeout for actions (60 seconds)
    navigation_timeout: int = 60000  # Default timeout for navigation (60 seconds)

    # Debug settings for troubleshooting automation issues
    debug_screenshots: bool = False  # Save screenshots at each step
    debug_logs: bool = False  # Enable detailed logging
    log_file: str = "logs/shiftee_debug.log"  # Log file path

    model_config = SettingsConfigDict(
        env_prefix="SHIFTEE_",
        env_file=(".env", "config/settings.toml"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def login_url(self) -> str:
        base = self.base_url.rstrip("/")
        return f"{base}/ko/accounts/login"


__all__ = ["ShifteeSettings"]
