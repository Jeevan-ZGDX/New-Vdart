import time
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import deque, Counter

from talkcraft.utils.logger import get_logger


class SpeechPatterns:
    def __init__(self):
        self._logger = get_logger("talkcraft.analysis.speech_patterns")
        self._word_history: deque = deque(maxlen=200)
        self._phrase_history: deque = deque(maxlen=100)
        self._repetition_history: List[Dict[str, Any]] = []
        self._max_history = 50

    def analyze(
        self,
        text: str,
        timestamp: float,
        duration: float,
        pace_wpm: float,
    ) -> Optional[Dict[str, Any]]:
        if not text or len(text.strip()) < 3:
            return None

        start = time.time()
        words = text.lower().split()
        word_count = len(words)
        if word_count == 0:
            return None

        self._word_history.extend(words)
        self._phrase_history.append({"text": text, "timestamp": timestamp, "words": words})

        repetition_result = self._detect_repetitions(words)
        sentence_result = self._analyze_sentences(text)
        pacing_result = self._analyze_pacing_variability(pace_wpm)

        result = {
            "timestamp": timestamp,
            "word_count": word_count,
            "repetition": repetition_result,
            "sentence": sentence_result,
            "pacing_variability": pacing_result,
            "processing_time": time.time() - start,
        }

        self._repetition_history.append(result)
        if len(self._repetition_history) > self._max_history:
            self._repetition_history = self._repetition_history[-self._max_history:]

        return result

    def _detect_repetitions(self, words: List[str]) -> Dict[str, Any]:
        if len(words) < 4:
            return {
                "has_repetition": False,
                "repeat_count": 0,
                "repeated_words": [],
                "repeated_phrases": [],
                "immediate_repeats": 0,
            }

        immediate_repeats = 0
        repeated_words = []
        word_counts: Dict[str, int] = {}

        for i in range(1, len(words)):
            if words[i] == words[i - 1]:
                immediate_repeats += 1
                if words[i] not in repeated_words:
                    repeated_words.append(words[i])

        short_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "is", "it", "i", "you", "we", "they"}
        for w in words:
            if w not in short_words:
                word_counts[w] = word_counts.get(w, 0) + 1

        frequent_words = {w: c for w, c in word_counts.items() if c >= 3 and len(w) > 2}
        sorted_frequent = sorted(frequent_words.items(), key=lambda x: -x[1])

        repeated_phrases = self._detect_phrase_repetitions(words)

        has_repetition = (
            immediate_repeats > 0
            or len(frequent_words) > 0
            or len(repeated_phrases) > 0
        )

        return {
            "has_repetition": has_repetition,
            "repeat_count": immediate_repeats,
            "repeated_words": [w for w, _ in sorted_frequent[:5]],
            "repeated_phrases": repeated_phrases[:3],
            "immediate_repeats": immediate_repeats,
            "frequent_words": dict(sorted_frequent[:5]),
        }

    def _detect_phrase_repetitions(self, words: List[str], min_len: int = 2, max_len: int = 4) -> List[str]:
        repeated = []
        seen = set()
        for phrase_len in range(min_len, min(max_len + 1, len(words))):
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len])
                if phrase in seen:
                    if phrase not in repeated:
                        repeated.append(phrase)
                else:
                    seen.add(phrase)
        return repeated

    def _analyze_sentences(self, text: str) -> Dict[str, Any]:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {
                "sentence_count": 0,
                "avg_words_per_sentence": 0,
                "max_words_per_sentence": 0,
                "has_run_ons": False,
                "has_fragments": False,
                "run_on_count": 0,
                "fragment_count": 0,
            }

        word_counts = [len(s.split()) for s in sentences]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        max_words = max(word_counts) if word_counts else 0
        min_words = min(word_counts) if word_counts else 0

        run_on_count = sum(1 for wc in word_counts if wc > 30)
        fragment_count = sum(1 for wc in word_counts if wc < 3)

        return {
            "sentence_count": len(sentences),
            "avg_words_per_sentence": round(avg_words, 1),
            "max_words_per_sentence": max_words,
            "min_words_per_sentence": min_words,
            "has_run_ons": run_on_count > 0,
            "has_fragments": fragment_count > 0,
            "run_on_count": run_on_count,
            "fragment_count": fragment_count,
        }

    def _analyze_pacing_variability(self, current_wpm: float) -> Dict[str, Any]:
        if current_wpm <= 0:
            return {
                "variability_score": 0.0,
                "is_monotone": False,
                "description": "neutral",
            }

        if current_wpm > 170:
            return {
                "variability_score": 0.9,
                "is_monotone": False,
                "description": "very_fast",
            }
        elif current_wpm > 150:
            return {
                "variability_score": 0.7,
                "is_monotone": False,
                "description": "fast",
            }
        elif current_wpm < 80:
            return {
                "variability_score": 0.3,
                "is_monotone": False,
                "description": "very_slow",
            }
        elif current_wpm < 100:
            return {
                "variability_score": 0.5,
                "is_monotone": False,
                "description": "slow",
            }

        return {
            "variability_score": 0.6,
            "is_monotone": False,
            "description": "moderate",
        }

    def get_session_repetition_rate(self) -> float:
        if not self._repetition_history:
            return 0.0
        total_repeats = sum(
            h.get("repetition", {}).get("repeat_count", 0)
            for h in self._repetition_history
        )
        total_words = sum(h.get("word_count", 0) for h in self._repetition_history)
        if total_words == 0:
            return 0.0
        return (total_repeats / total_words) * 100

    def reset(self):
        self._word_history.clear()
        self._phrase_history.clear()
        self._repetition_history.clear()
