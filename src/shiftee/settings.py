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

    # Timeout settings (milliseconds) - increased for macOS automation
    timeout: int = 60000  # Default timeout for actions (60 seconds)
    navigation_timeout: int = 60000  # Default timeout for navigation (60 seconds)

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
