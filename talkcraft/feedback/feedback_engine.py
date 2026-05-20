import time
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import deque

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


class FeedbackMessage:
    def __init__(
        self,
        category: str,
        message: str,
        priority: int = 0,
        severity: str = "info",
        actionable_tip: str = "",
        confidence: float = 0.5,
        trend: str = "stable",
        metric_value: Optional[float] = None,
    ):
        self.category = category
        self.message = message
        self.priority = priority
        self.severity = severity
        self.actionable_tip = actionable_tip
        self.confidence = confidence
        self.trend = trend
        self.metric_value = metric_value
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "message": self.message,
            "priority": self.priority,
            "severity": self.severity,
            "actionable_tip": self.actionable_tip,
            "confidence": round(self.confidence, 2),
            "trend": self.trend,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp,
        }


PACE_TIPS = {
    "too_fast": [
        "Pause briefly between sentences to reset your pace.",
        "Take a slow breath at each period — it naturally slows you down.",
        "Focus on enunciating each word clearly rather than rushing.",
        "Use short pauses as verbal punctuation — they help listeners digest.",
    ],
    "too_slow": [
        "Try speaking in slightly shorter phrases with fewer pauses.",
        "Prepare key points ahead — confidence speeds up delivery.",
        "Reduce pausing mid-sentence; save pauses for between ideas.",
    ],
}

FILLER_TIPS = {
    "um": "Replace 'um' with a brief silence — it sounds more confident.",
    "uh": "Pause instead of saying 'uh'. Silence is more powerful than filler.",
    "like": "Replace 'like' with 'for example', 'approximately', or a pause.",
    "you know": "Drop 'you know' — your audience trusts you. Just state the fact.",
    "actually": "Use 'actually' only when correcting. Otherwise, remove it.",
    "basically": "Replace 'basically' with nothing — your point stands on its own.",
    "literally": "Avoid 'literally' unless you mean something exactly. Most uses are figurative.",
    "so": "Try starting sentences without 'so'. It removes verbal hesitation.",
    "well": "Pause instead of starting with 'well'. It projects certainty.",
    "right": "Don't ask 'right?' after statements. Own your words.",
    "i mean": "Remove 'I mean' and state your point directly.",
    "sort of": "Replace 'sort of' with nothing. Be decisive.",
    "kind of": "Drop 'kind of'. Your opinion is valid without qualifiers.",
}

COMMON_GRAMMAR_TIPS = {
    "their/there/they're confusion": "their = possession, there = place, they're = they are",
    "your/you're confusion": "your = possession, you're = you are",
    "its/it's confusion": "its = possession, it's = it is",
    "to/too/two confusion": "to = direction, too = also/excess, two = number",
    "effect/affect confusion": "affect = verb (to influence), effect = noun (the result)",
}


class FeedbackEngine:
    def __init__(self):
        self._logger = get_logger("talkcraft.feedback")
        self._feedback_history: deque = deque(maxlen=100)
        self._suppressed_categories: Dict[str, float] = {}
        self._cooldowns = {
            "pace": config.feedback.pace_cooldown,
            "filler": config.feedback.filler_cooldown,
            "grammar": config.feedback.grammar_cooldown,
            "repetition": config.feedback.repetition_cooldown,
            "sentence": config.feedback.sentence_cooldown,
        }
        self._last_pace_status = "normal"
        self._session_start = time.time()
        self._total_feedback_count = 0

    def generate(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not analysis:
            return None

        start = time.time()
        messages: List[FeedbackMessage] = []
        text = analysis.get("text", "")

        if not text:
            return None

        rules = [
            self._check_pace,
            self._check_fillers,
            self._check_grammar,
            self._check_repetition,
            self._check_sentence_quality,
        ]

        for rule in rules:
            try:
                result = rule(analysis)
                if result:
                    messages.append(result)
            except Exception as e:
                self._logger.error(f"Feedback rule error: {e}")

        messages.sort(key=lambda m: (SEVERITY_ORDER.get(m.severity, 0), m.priority), reverse=True)

        active = []
        for msg in messages:
            cooldown = self._cooldowns.get(msg.category, 10.0)
            last = self._suppressed_categories.get(msg.category, 0.0)
            if (time.time() - last) >= cooldown:
                active.append(msg)
                self._suppressed_categories[msg.category] = time.time()

        for msg in active:
            self._feedback_history.append(msg)
            self._total_feedback_count += 1

        result = {
            "messages": [m.to_dict() for m in active[:3]],
            "message_count": len(active),
            "processing_time": time.time() - start,
            "source_text": text[:120],
            "session_duration": time.time() - self._session_start,
            "total_feedback_count": self._total_feedback_count,
        }

        return result

    def _check_pace(self, analysis: Dict[str, Any]) -> Optional[FeedbackMessage]:
        pace = analysis.get("pace")
        if not pace:
            return None

        status = pace.get("status", "normal")
        wpm = pace.get("current_wpm", 0)
        avg = pace.get("average_wpm", 0)
        severity_g = pace.get("severity", 0)
        trend = pace.get("trend", "stable")
        variability = pace.get("variability", {})

        if status == "too_fast" and severity_g >= 2:
            import random
            tip = random.choice(PACE_TIPS["too_fast"])
            self._last_pace_status = "too_fast"
            return FeedbackMessage(
                category="pace",
                message=f"Slow down — {wpm} words/min (target: {config.analysis.min_words_per_minute}-{config.analysis.max_words_per_minute})",
                priority=min(5, 2 + severity_g),
                severity="critical" if severity_g >= 4 else "warning",
                actionable_tip=tip,
                confidence=min(0.95, 0.6 + severity_g * 0.08),
                trend=trend,
                metric_value=wpm,
            )

        if status == "too_fast" and severity_g == 1:
            import random
            tip = random.choice(PACE_TIPS["too_fast"])
            self._last_pace_status = "too_fast"
            return FeedbackMessage(
                category="pace",
                message=f"Pace is slightly fast: {wpm} words/min",
                priority=2,
                severity="info",
                actionable_tip=tip,
                confidence=0.5,
                trend=trend,
                metric_value=wpm,
            )

        if status == "too_slow" and severity_g >= 1:
            import random
            tip = random.choice(PACE_TIPS["too_slow"])
            self._last_pace_status = "too_slow"
            return FeedbackMessage(
                category="pace",
                message=f"Pick up the pace — {wpm} words/min (target: {config.analysis.min_words_per_minute}-{config.analysis.max_words_per_minute})",
                priority=min(4, 1 + severity_g),
                severity="warning" if severity_g >= 2 else "info",
                actionable_tip=tip,
                confidence=min(0.85, 0.5 + severity_g * 0.1),
                trend=trend,
                metric_value=wpm,
            )

        if (status == "normal"
                and self._last_pace_status != "normal"
                and avg > 0
                and wpm > 0):
            self._last_pace_status = "normal"
            return FeedbackMessage(
                category="pace",
                message=f"Good pace — {wpm} words/min (avg: {avg})",
                priority=1,
                severity="info",
                actionable_tip="Maintain this comfortable speaking rhythm.",
                confidence=0.6,
                trend="stable",
                metric_value=wpm,
            )

        if (status == "normal"
                and variability.get("description") == "erratic"
                and len(list(analysis.get("pace_history", []))) > 5):
            return FeedbackMessage(
                category="pace",
                message="Speaking rate is uneven — vary your pace less",
                priority=2,
                severity="info",
                actionable_tip="Try to maintain a consistent rhythm. Read a paragraph aloud at one speed to practice.",
                confidence=0.5,
                trend=trend,
            )

        return None

    def _check_fillers(self, analysis: Dict[str, Any]) -> Optional[FeedbackMessage]:
        filler = analysis.get("filler")
        if not filler:
            return None

        count = filler.get("total_fillers", 0)
        rate = filler.get("filler_rate", 0)
        total_words = filler.get("total_words", 0)
        top_filler = filler.get("top_filler")
        density = filler.get("density", "low")
        trend = filler.get("trend", "stable")
        alternatives = filler.get("alternatives", [])

        if total_words < 5 or count == 0:
            return None

        if density == "high" and count >= 3:
            tip = FILLER_TIPS.get(top_filler, "")
            alt_text = ""
            if alternatives:
                alt_text = f" Try: {', '.join(alternatives[:2])}."

            trend_text = ""
            if trend == "improving":
                trend_text = " (improving)"
            elif trend == "worsening":
                trend_text = " (increasing)"

            return FeedbackMessage(
                category="filler",
                message=f"Too many filler words{trend_text}: {count} in {total_words} words ({rate}%)",
                priority=4,
                severity="critical" if rate > 20 else "warning",
                actionable_tip=tip + alt_text if tip else f"Pause instead of saying '{top_filler}'.",
                confidence=min(0.9, 0.5 + rate * 0.02),
                trend=trend,
                metric_value=rate,
            )

        if density == "medium" or (count >= 2 and rate > 8):
            tip = FILLER_TIPS.get(top_filler, "Try pausing instead of using filler words.")
            return FeedbackMessage(
                category="filler",
                message=f"Watch filler words: '{top_filler}' used {filler.get('filler_counts', {}).get(top_filler, 0)}x",
                priority=3,
                severity="warning",
                actionable_tip=tip,
                confidence=0.6,
                trend=trend,
                metric_value=rate,
            )

        return None

    def _check_grammar(self, analysis: Dict[str, Any]) -> Optional[FeedbackMessage]:
        grammar = analysis.get("grammar")
        if not grammar:
            return None

        error_count = grammar.get("error_count", 0)
        words = analysis.get("word_count", 0)
        error_types = grammar.get("error_types", {})

        if words < 3 or error_count == 0:
            return None

        top_errors = sorted(error_types.items(), key=lambda x: -x[1])[:2]
        error_details = "; ".join(f"{etype}: {count}x" for etype, count in top_errors)

        tips = []
        for etype, _ in top_errors:
            tip = COMMON_GRAMMAR_TIPS.get(etype, "")
            if tip:
                tips.append(tip)

        tip_text = " | ".join(tips) if tips else "Review your sentence structure."

        if error_count >= 2:
            return FeedbackMessage(
                category="grammar",
                message=f"Grammar issues: {error_details}",
                priority=3,
                severity="warning" if error_count >= 3 else "info",
                actionable_tip=tip_text,
                confidence=min(0.85, 0.4 + error_count * 0.1),
                trend="stable",
                metric_value=float(error_count),
            )

        return FeedbackMessage(
            category="grammar",
            message=f"Possible grammar issue: {list(error_types.keys())[0]}",
            priority=2,
            severity="info",
            actionable_tip=tip_text,
            confidence=0.4,
            trend="stable",
            metric_value=1.0,
        )

    def _check_repetition(self, analysis: Dict[str, Any]) -> Optional[FeedbackMessage]:
        patterns = analysis.get("speech_patterns")
        if not patterns:
            return None

        repetition = patterns.get("repetition", {})
        if not repetition or not repetition.get("has_repetition", False):
            return None

        repeat_count = repetition.get("repeat_count", 0)
        freq_words = repetition.get("frequent_words", {})
        phrases = repetition.get("repeated_phrases", [])

        messages_parts = []
        if repeat_count > 0:
            words = repetition.get("repeated_words", [])
            if words:
                messages_parts.append(f"repeating '{words[0]}'")

        if freq_words:
            top_word = list(freq_words.keys())[0]
            messages_parts.append(f"overusing '{top_word}' ({freq_words[top_word]}x)")

        if phrases:
            messages_parts.append(f"repeating phrase '{phrases[0]}'")

        if not messages_parts:
            return None

        msg = "; ".join(messages_parts)
        count = repeat_count + sum(freq_words.values())

        priority = min(4, 1 + count)
        severity = "warning" if count >= 3 else "info"

        tip = "Vary your word choice. Use a thesaurus or rephrase to avoid repeating the same word within a few sentences."

        return FeedbackMessage(
            category="repetition",
            message=f"Word repetition: {msg}",
            priority=priority,
            severity=severity,
            actionable_tip=tip,
            confidence=min(0.8, 0.3 + count * 0.1),
            trend="stable",
            metric_value=float(count),
        )

    def _check_sentence_quality(self, analysis: Dict[str, Any]) -> Optional[FeedbackMessage]:
        patterns = analysis.get("speech_patterns")
        if not patterns:
            return None

        sentence = patterns.get("sentence", {})
        if not sentence or sentence.get("sentence_count", 0) == 0:
            return None

        has_run_ons = sentence.get("has_run_ons", False)
        has_fragments = sentence.get("has_fragments", False)
        avg_words = sentence.get("avg_words_per_sentence", 0)
        max_words = sentence.get("max_words_per_sentence", 0)

        if has_run_ons and max_words > config.feedback.run_on_threshold:
            return FeedbackMessage(
                category="sentence",
                message=(
                    f"Very long sentence detected ({max_words} words). "
                    "Break it into shorter sentences for clarity."
                ),
                priority=3,
                severity="warning",
                actionable_tip=(
                    "Split long sentences at natural break points. "
                    "Aim for 15-20 words per sentence."
                ),
                confidence=0.7,
                trend="stable",
                metric_value=float(max_words),
            )

        if has_run_ons:
            return FeedbackMessage(
                category="sentence",
                message=f"Long sentence ({max_words} words) — consider breaking it up",
                priority=2,
                severity="info",
                actionable_tip="Listen for natural pauses where you could start a new sentence.",
                confidence=0.6,
                trend="stable",
                metric_value=float(max_words),
            )

        if has_fragments:
            return FeedbackMessage(
                category="sentence",
                message="Short sentence fragment detected — try completing the thought",
                priority=1,
                severity="info",
                actionable_tip="Fragments can sound abrupt. Add a main clause to complete the idea.",
                confidence=0.4,
                trend="stable",
            )

        if avg_words > 25:
            return FeedbackMessage(
                category="sentence",
                message=f"Sentences averaging {avg_words} words — aim for 15-20 for clarity",
                priority=1,
                severity="info",
                actionable_tip="Short sentences are easier for listeners to follow in real time.",
                confidence=0.5,
                trend="stable",
                metric_value=avg_words,
            )

        return None

    def get_history(self, count: int = 20) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in list(self._feedback_history)[-count:]]

    def get_session_summary(self) -> Dict[str, Any]:
        duration = time.time() - self._session_start
        categories: Dict[str, int] = {}
        severities: Dict[str, int] = {}
        for msg in self._feedback_history:
            categories[msg.category] = categories.get(msg.category, 0) + 1
            severities[msg.severity] = severities.get(msg.severity, 0) + 1

        return {
            "session_duration": round(duration, 1),
            "total_feedback": self._total_feedback_count,
            "categories": categories,
            "severities": severities,
            "top_concern": max(categories, key=categories.get) if categories else None,
        }

    def reset(self):
        self._feedback_history.clear()
        self._suppressed_categories.clear()
        self._last_pace_status = "normal"
        self._session_start = time.time()
        self._total_feedback_count = 0
