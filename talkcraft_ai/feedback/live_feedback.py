import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from talkcraft_ai.utils.logger import get_logger

logger = get_logger("live_feedback")


@dataclass
class FeedbackItem:
    category: str
    message: str
    severity: str
    score: float
    timestamp: float = field(default_factory=time.time)


FEEDBACK_COOLDOWN = 8.0


class LiveFeedbackEngine:
    def __init__(self):
        self._cooldowns: Dict[str, float] = {}
        self._feedback_history: List[FeedbackItem] = []

    def evaluate(self, scores: Dict) -> List[FeedbackItem]:
        items = []
        items.extend(self._evaluate_grammar(scores))
        items.extend(self._evaluate_filler(scores))
        items.extend(self._evaluate_pace(scores))
        items.extend(self._evaluate_engagement(scores))
        items.extend(self._evaluate_clarity(scores))
        items.extend(self._evaluate_confidence(scores))
        items.extend(self._evaluate_eye_contact(scores))
        items.sort(key=lambda x: self._severity_order(x.severity))
        for item in items:
            self._feedback_history.append(item)
        if len(self._feedback_history) > 100:
            self._feedback_history = self._feedback_history[-50:]
        return items

    def _can_show(self, category: str) -> bool:
        now = time.time()
        last = self._cooldowns.get(category, 0.0)
        return (now - last) >= FEEDBACK_COOLDOWN

    def _mark_shown(self, category: str) -> None:
        self._cooldowns[category] = time.time()

    def _severity_order(self, severity: str) -> int:
        return {"critical": 0, "warning": 1, "suggestion": 2, "positive": 3}.get(severity, 4)

    def _evaluate_grammar(self, scores: Dict) -> List[FeedbackItem]:
        grammar = scores.get("grammar", 0.5)
        items = []
        if grammar < 0.4 and self._can_show("grammar_low"):
            items.append(FeedbackItem(
                category="grammar",
                message="Watch your grammar — try using shorter, clearer sentences.",
                severity="warning",
                score=grammar,
            ))
            self._mark_shown("grammar_low")
        elif grammar > 0.85 and self._can_show("grammar_high"):
            items.append(FeedbackItem(
                category="grammar",
                message="Your grammar is excellent!",
                severity="positive",
                score=grammar,
            ))
            self._mark_shown("grammar_high")
        return items

    def _evaluate_filler(self, scores: Dict) -> List[FeedbackItem]:
        filler = scores.get("filler", 0.0)
        items = []
        if filler > 0.15 and self._can_show("filler_high"):
            items.append(FeedbackItem(
                category="fillers",
                message=f"Filler words at {filler:.0%} — try pausing instead of using fillers.",
                severity="warning",
                score=1.0 - filler,
            ))
            self._mark_shown("filler_high")
        elif 0.05 < filler <= 0.15 and self._can_show("filler_medium"):
            items.append(FeedbackItem(
                category="fillers",
                message="Notice your filler words. A short pause is more effective.",
                severity="suggestion",
                score=1.0 - filler,
            ))
            self._mark_shown("filler_medium")
        elif filler <= 0.02 and self._can_show("filler_low"):
            items.append(FeedbackItem(
                category="fillers",
                message="Great control over filler words!",
                severity="positive",
                score=1.0,
            ))
            self._mark_shown("filler_low")
        return items

    def _evaluate_pace(self, scores: Dict) -> List[FeedbackItem]:
        pace = scores.get("pace", 0.5)
        items = []
        if pace < 0.3 and self._can_show("pace_slow"):
            items.append(FeedbackItem(
                category="pace",
                message="Your pace is slow — try to speak a bit more fluently.",
                severity="suggestion",
                score=pace,
            ))
            self._mark_shown("pace_slow")
        elif pace > 0.9 and self._can_show("pace_fast"):
            items.append(FeedbackItem(
                category="pace",
                message="Your pace is good but could be slightly slower for clarity.",
                severity="suggestion",
                score=pace,
            ))
            self._mark_shown("pace_fast")
        elif 0.6 <= pace <= 0.85 and self._can_show("pace_good"):
            items.append(FeedbackItem(
                category="pace",
                message="Your speaking pace is well-balanced!",
                severity="positive",
                score=pace,
            ))
            self._mark_shown("pace_good")
        return items

    def _evaluate_engagement(self, scores: Dict) -> List[FeedbackItem]:
        engagement = scores.get("engagement", 0.0)
        items = []
        if engagement < 0.3 and self._can_show("engagement_low"):
            items.append(FeedbackItem(
                category="engagement",
                message="Try to be more engaged — ask questions and share your thoughts.",
                severity="warning",
                score=engagement,
            ))
            self._mark_shown("engagement_low")
        elif 0.3 <= engagement < 0.6 and self._can_show("engagement_medium"):
            items.append(FeedbackItem(
                category="engagement",
                message="Good engagement! Try expanding your responses with examples.",
                severity="suggestion",
                score=engagement,
            ))
            self._mark_shown("engagement_medium")
        elif engagement >= 0.8 and self._can_show("engagement_high"):
            items.append(FeedbackItem(
                category="engagement",
                message="Excellent engagement in the conversation!",
                severity="positive",
                score=engagement,
            ))
            self._mark_shown("engagement_high")
        return items

    def _evaluate_clarity(self, scores: Dict) -> List[FeedbackItem]:
        clarity = scores.get("clarity", 0.0)
        items = []
        if clarity < 0.3 and self._can_show("clarity_low"):
            items.append(FeedbackItem(
                category="clarity",
                message="Your responses could be clearer — try structuring your thoughts before speaking.",
                severity="warning",
                score=clarity,
            ))
            self._mark_shown("clarity_low")
        elif clarity > 0.85 and self._can_show("clarity_high"):
            items.append(FeedbackItem(
                category="clarity",
                message="Your thoughts are very clear and well-structured!",
                severity="positive",
                score=clarity,
            ))
            self._mark_shown("clarity_high")
        return items

    def _evaluate_confidence(self, scores: Dict) -> List[FeedbackItem]:
        confidence = scores.get("confidence", 0.0)
        items = []
        if confidence < 0.3 and self._can_show("confidence_low"):
            items.append(FeedbackItem(
                category="confidence",
                message="Try to project more confidence — maintain steady eye contact and speak clearly.",
                severity="suggestion",
                score=confidence,
            ))
            self._mark_shown("confidence_low")
        elif confidence > 0.8 and self._can_show("confidence_high"):
            items.append(FeedbackItem(
                category="confidence",
                message="You appear confident and in control!",
                severity="positive",
                score=confidence,
            ))
            self._mark_shown("confidence_high")
        return items

    def _evaluate_eye_contact(self, scores: Dict) -> List[FeedbackItem]:
        eye_contact = scores.get("eye_contact", 0.0)
        items = []
        if eye_contact < 0.3 and self._can_show("eye_contact_low"):
            items.append(FeedbackItem(
                category="eye_contact",
                message="Try to maintain more eye contact with the camera.",
                severity="suggestion",
                score=eye_contact,
            ))
            self._mark_shown("eye_contact_low")
        elif eye_contact > 0.85 and self._can_show("eye_contact_high"):
            items.append(FeedbackItem(
                category="eye_contact",
                message="Great eye contact!",
                severity="positive",
                score=eye_contact,
            ))
            self._mark_shown("eye_contact_high")
        return items

    def get_recent_feedback(self, limit: int = 10) -> List[FeedbackItem]:
        return self._feedback_history[-limit:]

    def reset(self) -> None:
        self._cooldowns.clear()
        self._feedback_history.clear()
