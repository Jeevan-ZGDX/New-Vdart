import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_duration: float = 2.0
    channels: int = 1
    dtype: str = "int16"
    blocksize: int = 8192
    device: Optional[int] = None
    silence_threshold: float = 0.01

    @property
    def chunk_samples(self) -> int:
        return int(self.sample_rate * self.chunk_duration)


@dataclass
class TranscriptionConfig:
    model_size: str = "tiny.en"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "en"
    beam_size: int = 1
    best_of: int = 1
    patience: float = 0.0
    vad_filter: bool = True
    vad_parameters: dict = field(default_factory=lambda: {
        "threshold": 0.5,
        "min_speech_duration_ms": 250,
        "min_silence_duration_ms": 100,
        "speech_pad_ms": 400,
    })


@dataclass
class QueueConfig:
    audio_queue_maxsize: int = 10
    transcription_queue_maxsize: int = 10
    analysis_queue_maxsize: int = 20
    feedback_queue_maxsize: int = 20


@dataclass
class AnalysisConfig:
    filler_words: List[str] = field(default_factory=lambda: [
        "um", "uh", "ah", "er", "like", "you know",
        "actually", "basically", "literally", "so",
        "well", "right", "okay", "i mean", "you see",
        "sort of", "kind of", "i guess", "you know what i mean",
    ])
    max_words_per_minute: float = 160.0
    min_words_per_minute: float = 100.0
    grammar_language: str = "en-US"


@dataclass
class FeedbackConfig:
    pace_cooldown: float = 12.0
    filler_cooldown: float = 10.0
    grammar_cooldown: float = 8.0
    repetition_cooldown: float = 15.0
    sentence_cooldown: float = 12.0
    filler_high_threshold: float = 15.0
    filler_medium_threshold: float = 8.0
    repetition_min_words: int = 3
    run_on_threshold: int = 30
    fragment_max_words: int = 3


@dataclass
class UIConfig:
    refresh_interval_ms: int = 250
    max_transcription_history: int = 50
    show_timestamps: bool = True


@dataclass
class AppConfig:
    audio: AudioConfig = field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    queues: QueueConfig = field(default_factory=QueueConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    log_level: str = "INFO"
    log_file: Optional[str] = "talkcraft.log"

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "AppConfig":
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


config = AppConfig()
