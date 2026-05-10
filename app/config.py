from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"


class TradingMode(str, Enum):
    PAPER = "PAPER"
    ORDER_TEST = "ORDER_TEST"
    LIVE_DISABLED = "LIVE_DISABLED"
    LIVE = "LIVE"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field("local", alias="APP_ENV")
    app_timezone: str = Field("Asia/Seoul", alias="APP_TIMEZONE")
    app_name: str = Field("ASTT", alias="APP_NAME")
    database_url: str = Field("sqlite:///data_store/app.sqlite", alias="DATABASE_URL")

    upbit_base_url: str = Field("https://api.upbit.com", alias="UPBIT_BASE_URL")
    upbit_ws_public_url: str = Field("wss://api.upbit.com/websocket/v1", alias="UPBIT_WS_PUBLIC_URL")
    upbit_access_key: str = Field("", alias="UPBIT_ACCESS_KEY")
    upbit_secret_key: str = Field("", alias="UPBIT_SECRET_KEY")
    upbit_allowed_ip: str = Field("", alias="UPBIT_ALLOWED_IP")

    trading_mode: TradingMode = Field(TradingMode.PAPER, alias="TRADING_MODE")
    live_trading_enabled: bool = Field(False, alias="LIVE_TRADING_ENABLED")
    order_test_enabled: bool = Field(True, alias="ORDER_TEST_ENABLED")

    virtual_cash_krw: float = Field(1_000_000, alias="VIRTUAL_CASH_KRW")
    max_daily_loss_pct: float = Field(1.5, alias="MAX_DAILY_LOSS_PCT")
    daily_target_pct: float = Field(1.0, alias="DAILY_TARGET_PCT")
    min_order_krw: float = Field(5_000, alias="MIN_ORDER_KRW")
    max_order_krw: float = Field(10_000, alias="MAX_ORDER_KRW")
    max_open_positions: int = Field(5, alias="MAX_OPEN_POSITIONS")

    kst_open_scan_start: str = Field("08:50", alias="KST_OPEN_SCAN_START")
    kst_open_monitor_start: str = Field("09:00", alias="KST_OPEN_MONITOR_START")
    kst_open_decision_time: str = Field("09:03", alias="KST_OPEN_DECISION_TIME")
    kst_open_trade_end: str = Field("09:30", alias="KST_OPEN_TRADE_END")
    max_scan_markets: int = Field(50, alias="MAX_SCAN_MARKETS")

    min_mr_k_score: float = Field(50, alias="MIN_MR_K_SCORE")
    min_maggie_score: float = Field(85, alias="MIN_MAGGIE_SCORE")
    min_rezo_score: float = Field(80, alias="MIN_REZO_SCORE")
    min_costa_score: float = Field(60, alias="MIN_COSTA_SCORE")
    min_iris_score: float = Field(75, alias="MIN_IRIS_SCORE")
    min_final_score: float = Field(80, alias="MIN_FINAL_SCORE")

    enable_costa_dca: bool = Field(False, alias="ENABLE_COSTA_DCA")
    costa_step_1_krw: float = Field(10_000, alias="COSTA_STEP_1_KRW")
    costa_step_2_krw: float = Field(20_000, alias="COSTA_STEP_2_KRW")
    costa_step_3_krw: float = Field(30_000, alias="COSTA_STEP_3_KRW")
    costa_take_profit_pct: float = Field(0.8, alias="COSTA_TAKE_PROFIT_PCT")
    costa_max_exposure_per_market_krw: float = Field(60_000, alias="COSTA_MAX_EXPOSURE_PER_MARKET_KRW")

    taker_fee_pct: float = Field(0.05, alias="TAKER_FEE_PCT")
    default_slippage_pct: float = Field(0.15, alias="DEFAULT_SLIPPAGE_PCT")
    conservative_fill_mode: bool = Field(True, alias="CONSERVATIVE_FILL_MODE")

    upbit_quotation_rps_limit: int = Field(8, alias="UPBIT_QUOTATION_RPS_LIMIT")
    upbit_order_rps_limit: int = Field(4, alias="UPBIT_ORDER_RPS_LIMIT")
    rate_limit_backoff_seconds: float = Field(1.0, alias="RATE_LIMIT_BACKOFF_SECONDS")

    store_raw_ticks: bool = Field(False, alias="STORE_RAW_TICKS")
    tick_retention_hours: int = Field(24, alias="TICK_RETENTION_HOURS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @field_validator("trading_mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.upper()
        return value

    @model_validator(mode="after")
    def validate_operating_mode(self) -> "Settings":
        if self.trading_mode == TradingMode.LIVE and self.live_trading_enabled is not True:
            raise RuntimeError("LIVE mode requires LIVE_TRADING_ENABLED=true")
        if self.trading_mode == TradingMode.ORDER_TEST and not self.has_upbit_keys:
            raise RuntimeError("ORDER_TEST mode requires UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY")
        return self

    @property
    def has_upbit_keys(self) -> bool:
        return bool(self.upbit_access_key and self.upbit_secret_key)

    @property
    def data_store_dir(self) -> Path:
        return ROOT_DIR / "data_store"

    @property
    def reports_dir(self) -> Path:
        return ROOT_DIR / "reports"

    def ensure_dirs(self) -> None:
        self.data_store_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


def get_settings(**overrides: Any) -> Settings:
    load_dotenv(ENV_PATH, override=False)
    settings = Settings(**overrides)
    settings.ensure_dirs()
    return settings


def safe_settings_summary(settings: Settings) -> dict[str, Any]:
    return {
        "app": settings.app_name,
        "mode": settings.trading_mode.value,
        "live_trading_enabled": settings.live_trading_enabled,
        "order_test_enabled": settings.order_test_enabled,
        "has_upbit_keys": settings.has_upbit_keys,
        "database_url": settings.database_url,
    }

