from dataclasses import dataclass, field
from typing import List, Dict, Optional
import statistics


DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced", "expert"]


@dataclass
class PerformanceMetrics:
    grammar_score: List[float] = field(default_factory=list)
    filler_score: List[float] = field(default_factory=list)
    pace_score: List[float] = field(default_factory=list)
    clarity_score: List[float] = field(default_factory=list)
    engagement_score: List[float] = field(default_factory=list)
    response_relevance: List[float] = field(default_factory=list)

    def add_scores(self, grammar: float = 0.0, filler: float = 0.0,
                   pace: float = 0.0, clarity: float = 0.0,
                   engagement: float = 0.0, relevance: float = 0.0) -> None:
        if grammar > 0:
            self.grammar_score.append(grammar)
        if filler > 0:
            self.filler_score.append(filler)
        if pace > 0:
            self.pace_score.append(pace)
        if clarity > 0:
            self.clarity_score.append(clarity)
        if engagement > 0:
            self.engagement_score.append(engagement)
        if relevance > 0:
            self.response_relevance.append(relevance)

    def average(self) -> float:
        scores = []
        if self.grammar_score:
            scores.append(statistics.mean(self.grammar_score))
        if self.filler_score:
            scores.append(statistics.mean(self.filler_score))
        if self.pace_score:
            scores.append(statistics.mean(self.pace_score))
        if self.clarity_score:
            scores.append(statistics.mean(self.clarity_score))
        if self.engagement_score:
            scores.append(statistics.mean(self.engagement_score))
        if self.response_relevance:
            scores.append(statistics.mean(self.response_relevance))
        return statistics.mean(scores) if scores else 0.0


class DifficultyAdapter:
    def __init__(self, initial_level: str = "intermediate"):
        self._level = initial_level if initial_level in DIFFICULTY_LEVELS else "intermediate"
        self._level_idx = DIFFICULTY_LEVELS.index(self._level)
        self._metrics = PerformanceMetrics()
        self._consecutive_good: int = 0
        self._consecutive_poor: int = 0
        self._adaptation_threshold_good: int = 5
        self._adaptation_threshold_poor: int = 3

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, value: str) -> None:
        if value in DIFFICULTY_LEVELS:
            self._level = value
            self._level_idx = DIFFICULTY_LEVELS.index(value)

    @property
    def level_index(self) -> int:
        return self._level_idx

    @property
    def metrics(self) -> PerformanceMetrics:
        return self._metrics

    def update(self, grammar: float = 0.0, filler: float = 0.0,
               pace: float = 0.0, clarity: float = 0.0,
               engagement: float = 0.0, relevance: float = 0.0) -> str:
        self._metrics.add_scores(
            grammar=grammar,
            filler=filler,
            pace=pace,
            clarity=clarity,
            engagement=engagement,
            relevance=relevance,
        )
        if self._metrics.average() >= 0.75:
            self._consecutive_good += 1
            self._consecutive_poor = 0
        elif self._metrics.average() <= 0.4:
            self._consecutive_poor += 1
            self._consecutive_good = 0
        else:
            self._consecutive_good = 0
            self._consecutive_poor = 0
        return self._adapt()

    def _adapt(self) -> str:
        old_level = self._level
        if self._consecutive_good >= self._adaptation_threshold_good:
            if self._level_idx < len(DIFFICULTY_LEVELS) - 1:
                self._level_idx += 1
                self._level = DIFFICULTY_LEVELS[self._level_idx]
                self._consecutive_good = 0
        elif self._consecutive_poor >= self._adaptation_threshold_poor:
            if self._level_idx > 0:
                self._level_idx -= 1
                self._level = DIFFICULTY_LEVELS[self._level_idx]
                self._consecutive_poor = 0
        if old_level != self._level:
            return f"difficulty_changed:{old_level}->{self._level}"
        return ""

    def get_difficulty_prompt_addition(self) -> str:
        prompts = {
            "beginner": (
                "Use simple vocabulary and short sentences. "
                "Be encouraging and supportive. "
                "Ask straightforward questions."
            ),
            "intermediate": (
                "Use moderate vocabulary and normal sentence complexity. "
                "Ask questions that require some thought."
            ),
            "advanced": (
                "Use sophisticated vocabulary and complex sentence structures. "
                "Ask challenging questions that require analysis."
            ),
            "expert": (
                "Use advanced vocabulary and complex argumentation. "
                "Ask深入 questions requiring critical thinking. "
                "Challenge the user's ideas and push for depth."
            ),
        }
        return prompts.get(self._level, prompts["intermediate"])

    def reset(self) -> None:
        self._level = "intermediate"
        self._level_idx = DIFFICULTY_LEVELS.index(self._level)
        self._metrics = PerformanceMetrics()
        self._consecutive_good = 0
        self._consecutive_poor = 0
