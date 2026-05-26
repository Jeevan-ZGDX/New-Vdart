import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///./talkcraft_coach.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class AuthConfig:
    secret_key: str = "change-this-to-a-secure-random-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30


@dataclass
class AnalyticsConfig:
    trend_window_days: int = 30
    weakness_detection_threshold: float = 0.6
    improvement_detection_min_sessions: int = 3
    weekly_summary_day: str = "monday"
    session_replay_batch_size: int = 100


@dataclass
class CoachingConfig:
    adaptive_difficulty_enabled: bool = True
    beginner_threshold: float = 0.5
    intermediate_threshold: float = 0.7
    advanced_threshold: float = 0.85
    practice_recommendation_count: int = 3
    improvement_plan_max_focus_areas: int = 3
    learning_path_max_exercises: int = 10


@dataclass
class GamificationConfig:
    enabled: bool = True
    achievement_check_interval_seconds: int = 60
    notify_on_unlock: bool = True


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "info"
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class IntegrationConfig:
    speech_server_url: str = "http://localhost:8000"
    vision_server_url: str = "http://localhost:8765"
    ai_server_url: str = "http://localhost:8002"
    sync_interval_seconds: int = 30


@dataclass
class AppConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    coaching: CoachingConfig = field(default_factory=CoachingConfig)
    gamification: GamificationConfig = field(default_factory=GamificationConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)

    _instance: Optional["AppConfig"] = None
    _config_dir: Optional[Path] = None

    @classmethod
    def get_instance(cls) -> "AppConfig":
        if cls._instance is None:
            cls._instance = cls._load()
        return cls._instance

    @classmethod
    def _config_path(cls) -> Path:
        if cls._config_dir is None:
            cls._config_dir = Path(__file__).resolve().parent.parent
        return cls._config_dir / "config.json"

    @classmethod
    def _load(cls) -> "AppConfig":
        path = cls._config_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cfg = cls()
                for section, values in data.items():
                    section_cfg = getattr(cfg, section, None)
                    if section_cfg is not None and isinstance(values, dict):
                        for k, v in values.items():
                            if hasattr(section_cfg, k):
                                setattr(section_cfg, k, v)
                return cfg
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        path = self._config_path()
        data = {}
        for section_name in self._sections():
            data[section_name] = asdict(getattr(self, section_name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _sections(self):
        return ["database", "auth", "analytics", "coaching", "gamification", "server", "integration"]


config = AppConfig.get_instance()
