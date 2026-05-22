import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class LLMConfig:
    api_base: str = "http://localhost:11434/v1"
    api_key: str = "sk-placeholder"
    model: str = "llama3.2:1b"
    temperature: float = 0.7
    max_tokens: int = 256
    top_p: float = 0.9
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.3
    timeout: float = 30.0
    streaming: bool = True


@dataclass
class TTSConfig:
    enabled: bool = True
    rate: int = 180
    volume: float = 0.9
    voice_id: Optional[int] = None


@dataclass
class ConversationConfig:
    mode: str = "casual_conversation"
    topic: str = ""
    difficulty: str = "intermediate"
    max_history_turns: int = 10
    silence_timeout: float = 1.5
    utterance_min_duration: float = 0.5
    enable_followup: bool = True


@dataclass
class ScoringConfig:
    grammar_weight: float = 0.15
    filler_weight: float = 0.10
    pace_weight: float = 0.10
    eye_contact_weight: float = 0.10
    posture_weight: float = 0.10
    hand_gesture_weight: float = 0.05
    engagement_weight: float = 0.15
    clarity_weight: float = 0.15
    confidence_weight: float = 0.10


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_duration: float = 2.0
    channels: int = 1
    dtype: str = "int16"
    blocksize: int = 8192
    device: Optional[int] = None


@dataclass
class DashboardConfig:
    refresh_interval_ms: int = 250
    max_transcript_items: int = 50
    port: int = 8502


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
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
        for section_name in self._sections():
            data[section_name] = asdict(getattr(self, section_name))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _sections(self):
        return [
            "llm", "tts", "conversation", "scoring",
            "audio", "dashboard", "server",
        ]


config = AppConfig.get_instance()
