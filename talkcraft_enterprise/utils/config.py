import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///./talkcraft_enterprise.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class MultilingualConfig:
    enabled: bool = True
    supported_languages: list = field(default_factory=lambda: ["en", "hi", "ta", "es", "fr"])
    default_language: str = "en"
    pronunciation_sensitivity: float = 0.7


@dataclass
class AvatarConfig:
    enabled: bool = True
    max_avatars_per_room: int = 6
    animation_fps: int = 10
    lip_sync_enabled: bool = True
    default_avatar: str = "coach"


@dataclass
class CollaborationConfig:
    max_participants_per_room: int = 10
    room_timeout_minutes: int = 60
    max_rooms_per_user: int = 5


@dataclass
class EnterpriseConfig:
    enabled: bool = True
    team_report_interval_days: int = 7
    max_teams_per_org: int = 50


@dataclass
class CertificationConfig:
    passing_score: float = 0.7
    max_attempts_per_day: int = 3
    levels: list = field(default_factory=lambda: ["bronze", "silver", "gold", "platinum"])


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8005
    log_level: str = "info"
    cors_origins: list = field(default_factory=lambda: ["*"])


@dataclass
class AppConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    multilingual: MultilingualConfig = field(default_factory=MultilingualConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    collaboration: CollaborationConfig = field(default_factory=CollaborationConfig)
    enterprise: EnterpriseConfig = field(default_factory=EnterpriseConfig)
    certification: CertificationConfig = field(default_factory=CertificationConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

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
        for section_name in ["database", "multilingual", "avatar", "collaboration", "enterprise", "certification", "server"]:
            data[section_name] = asdict(getattr(self, section_name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


config = AppConfig.get_instance()
