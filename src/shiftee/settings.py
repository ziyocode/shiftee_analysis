from pydantic_settings import BaseSettings, SettingsConfigDict


class ShifteeSettings(BaseSettings):
    """Configuration for Shiftee automation."""

    id: str
    password: str
    headless: bool = True
    base_url: str = "https://shiftee.io"
    calendar_url: str | None = None
    report_url: str | None = None
    attendance_list_url: str | None = None

    # 분석 필터
    team_filter: str | None = None  # 특정 팀만 분석 (쉼표 구분 다중 입력 가능, 예: "뱅킹IS팀,뱅킹통신보안팀")
    exclude_role: str | None = "교대제"  # 제외할 직무

    # 알림
    slack_webhook_url: str | None = None  # Slack Incoming Webhook URL

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

    @property
    def team_filter_list(self) -> list[str]:
        """쉼표로 구분된 팀 필터를 리스트로 반환. 비어있으면 빈 리스트."""
        if not self.team_filter:
            return []
        return [t.strip() for t in self.team_filter.split(",") if t.strip()]


__all__ = ["ShifteeSettings"]
