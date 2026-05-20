import time
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


FILLER_ALTERNATIVES = {
    "um": ["pause briefly", "take a breath"],
    "uh": ["pause briefly", "collect your thought"],
    "ah": ["pause briefly"],
    "er": ["pause briefly"],
    "like": ["approximately", "such as", "for example", "around"],
    "you know": ["as you may know", "notably", "specifically"],
    "actually": ["in fact", "as a matter of fact"],
    "basically": ["essentially", "fundamentally", "in short"],
    "literally": ["figuratively", "virtually", "truly"],
    "so": ["therefore", "thus", "consequently", "accordingly"],
    "well": ["indeed", "certainly"],
    "right": ["correct", "precisely", "indeed"],
    "okay": ["alright", "agreed", "understood"],
    "i mean": ["that is", "in other words", "namely"],
    "you see": ["as you can see", "evidently"],
    "sort of": ["somewhat", "rather", "partially"],
    "kind of": ["somewhat", "rather", "moderately"],
    "i guess": ["presumably", "perhaps", "I believe"],
    "you know what i mean": ["in essence", "to clarify"],
}


class FillerDetector:
    def __init__(self):
        self._logger = get_logger("talkcraft.analysis.filler")
        self._filler_words = config.analysis.filler_words
        self._total_filler_count = 0
        self._total_word_count = 0
        self._filler_history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._per_word_totals: Dict[str, int] = defaultdict(int)

        self._filler_patterns = [
            re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            for word in self._filler_words
        ]

        self._multi_word_patterns = []
        for word in self._filler_words:
            if " " in word:
                self._multi_word_patterns.append(
                    (word, re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE))
                )

    def detect(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or len(text.strip()) < 2:
            return None

        start = time.time()
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return None

        filler_counts: Dict[str, int] = {}
        total_fillers = 0

        for i, pattern in enumerate(self._filler_patterns):
            matches = pattern.findall(text)
            if matches:
                word = self._filler_words[i]
                filler_counts[word] = len(matches)
                total_fillers += len(matches)
                self._per_word_totals[word] += len(matches)

        filler_rate = (total_fillers / word_count) * 100 if word_count > 0 else 0.0
        avg_rate = self.get_average_filler_rate()

        top_filler = max(filler_counts, key=filler_counts.get) if filler_counts else None
        alternatives = FILLER_ALTERNATIVES.get(top_filler, []) if top_filler else []

        density = "low"
        if filler_rate > 15:
            density = "high"
        elif filler_rate > 8:
            density = "medium"

        result = {
            "total_fillers": total_fillers,
            "filler_counts": filler_counts,
            "filler_rate": round(filler_rate, 1),
            "avg_filler_rate": round(avg_rate, 1),
            "total_words": word_count,
            "top_filler": top_filler,
            "alternatives": alternatives,
            "density": density,
            "trend": self._compute_trend(filler_rate),
            "processing_time": time.time() - start,
        }

        self._total_filler_count += total_fillers
        self._total_word_count += word_count

        self._filler_history.append(result)
        if len(self._filler_history) > self._max_history:
            self._filler_history = self._filler_history[-self._max_history:]

        return result

    def _compute_trend(self, current_rate: float) -> str:
        if len(self._filler_history) < 5:
            return "stable"
        recent = [h["filler_rate"] for h in self._filler_history[-5:]]
        if current_rate < recent[0] * 0.8:
            return "improving"
        elif current_rate > recent[0] * 1.2:
            return "worsening"
        return "stable"

    def get_average_filler_rate(self) -> float:
        total_fillers = sum(h["total_fillers"] for h in self._filler_history)
        total_words = sum(h["total_words"] for h in self._filler_history)
        if total_words == 0:
            return 0.0
        return (total_fillers / total_words) * 100

    def get_most_used_fillers(self, top_n: int = 5) -> List[Tuple[str, int]]:
        sorted_words = sorted(
            self._per_word_totals.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_words[:top_n]

    def get_filler_alternatives(self, filler_word: str) -> List[str]:
        return FILLER_ALTERNATIVES.get(filler_word.lower(), [])

    @property
    def filler_words_list(self) -> List[str]:
        return self._filler_words

    def reset(self):
        self._total_filler_count = 0
        self._total_word_count = 0
        self._filler_history.clear()
        self._per_word_totals.clear()
