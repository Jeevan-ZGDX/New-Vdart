import re
from dataclasses import dataclass, field

from talkcraft_ai.utils.logger import get_logger

logger = get_logger("clarity_scorer")


@dataclass
class ClarityScores:
    overall: float = 0.0
    sentence_structure: float = 0.0
    vocabulary_richness: float = 0.0
    coherence: float = 0.0
    conciseness: float = 0.0
    filler_impact: float = 0.0


class ClarityScorer:
    def __init__(self):
        self._common_fillers = {
            "um", "uh", "like", "well", "you know", "actually", "basically",
            "literally", "sort of", "kind of", "i mean", "right", "so",
        }

    def score(self, text: str, filler_rate: float = 0.0) -> ClarityScores:
        scores = ClarityScores()
        if not text or not text.strip():
            return scores
        scores.sentence_structure = self._score_sentence_structure(text)
        scores.vocabulary_richness = self._score_vocabulary_richness(text)
        scores.coherence = self._score_coherence(text)
        scores.conciseness = self._score_conciseness(text)
        scores.filler_impact = self._score_filler_impact(filler_rate)
        weights = {
            "sentence_structure": 0.25,
            "vocabulary_richness": 0.20,
            "coherence": 0.25,
            "conciseness": 0.15,
            "filler_impact": 0.15,
        }
        scores.overall = (
            scores.sentence_structure * weights["sentence_structure"]
            + scores.vocabulary_richness * weights["vocabulary_richness"]
            + scores.coherence * weights["coherence"]
            + scores.conciseness * weights["conciseness"]
            + scores.filler_impact * weights["filler_impact"]
        )
        return scores

    def _score_sentence_structure(self, text: str) -> float:
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if not sentences:
            return 0.3
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if 5 <= avg_words <= 20:
            structure_score = 0.9
        elif avg_words < 5:
            structure_score = 0.5
        elif avg_words <= 30:
            structure_score = 0.7
        else:
            structure_score = 0.4
        complete_sentences = sum(
            1 for s in sentences
            if re.match(r'^[A-Z"\'(]', s.strip()) and s.strip()[-1] in ".!?"
        )
        completeness_ratio = complete_sentences / len(sentences) if sentences else 0
        return structure_score * 0.6 + completeness_ratio * 0.4

    def _score_vocabulary_richness(self, text: str) -> float:
        words = text.lower().split()
        if len(words) < 5:
            return 0.5
        unique_words = set(words)
        type_token_ratio = len(unique_words) / len(words)
        if type_token_ratio > 0.7:
            return 0.9
        elif type_token_ratio > 0.5:
            return 0.7
        elif type_token_ratio > 0.3:
            return 0.5
        else:
            return 0.3

    def _score_coherence(self, text: str) -> float:
        transition_words = {
            "however", "therefore", "furthermore", "moreover", "nevertheless",
            "consequently", "additionally", "also", "then", "next", "first",
            "second", "finally", "in addition", "for example", "for instance",
            "on the other hand", "in contrast", "similarly", "because",
            "so", "thus", "hence", "accordingly", "as a result",
        }
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) <= 1:
            return 0.6
        text_lower = text.lower()
        transition_count = sum(1 for tw in transition_words if tw in text_lower)
        expected = max(1, len(sentences) * 0.3)
        ratio = min(1.0, transition_count / expected)
        sentence_lengths = [len(s.split()) for s in sentences]
        if len(sentence_lengths) > 1:
            import statistics
            cv = statistics.stdev(sentence_lengths) / max(statistics.mean(sentence_lengths), 1)
            consistency = max(0, 1.0 - cv)
        else:
            consistency = 0.7
        return ratio * 0.5 + consistency * 0.5

    def _score_conciseness(self, text: str) -> float:
        words = len(text.split())
        if words < 10:
            return 0.6
        elif words < 30:
            return 0.9
        elif words < 60:
            return 0.7
        elif words < 100:
            return 0.5
        else:
            return 0.3

    def _score_filler_impact(self, filler_rate: float) -> float:
        if filler_rate <= 0.02:
            return 1.0
        elif filler_rate <= 0.05:
            return 0.8
        elif filler_rate <= 0.10:
            return 0.6
        elif filler_rate <= 0.15:
            return 0.4
        else:
            return 0.2
