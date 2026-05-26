from typing import Dict, List, Optional

EXPRESSION_FEATURES = {
    "neutral": {"eyes": "open", "eyebrows": "relaxed", "mouth": "closed"},
    "smiling": {"eyes": "squint", "eyebrows": "raised", "mouth": "smile"},
    "attentive": {"eyes": "wide", "eyebrows": "raised", "mouth": "slight_open"},
    "thoughtful": {"eyes": "squint", "eyebrows": "furrowed", "mouth": "pursed"},
    "surprised": {"eyes": "wide", "eyebrows": "raised", "mouth": "open"},
    "nodding": {"eyes": "open", "eyebrows": "relaxed", "mouth": "closed", "action": "nod"},
    "listening": {"eyes": "open", "eyebrows": "slightly_raised", "mouth": "closed", "action": "slight_nod"},
    "observing": {"eyes": "narrowed", "eyebrows": "relaxed", "mouth": "closed"},
    "speaking": {"eyes": "open", "eyebrows": "animated", "mouth": "talking"},
}

LIP_SYNC_PHONEMES = {
    "A": {"mouth": "wide_open"}, "E": {"mouth": "slight_open"},
    "I": {"mouth": "wide_smile"}, "O": {"mouth": "rounded_open"},
    "U": {"mouth": "pursed"}, "M": {"mouth": "closed"},
    "F": {"mouth": "lip_bite"}, "default": {"mouth": "slight_open"},
}


class ExpressionMapper:
    def get_expression(self, emotion: str) -> Dict:
        return EXPRESSION_FEATURES.get(emotion, EXPRESSION_FEATURES["neutral"])

    def get_lip_sync(self, phoneme: str) -> Dict:
        return LIP_SYNC_PHONEMES.get(phoneme, LIP_SYNC_PHONEMES["default"])

    def map_score_to_expression(self, score: float) -> str:
        if score >= 0.9:
            return "surprised"
        if score >= 0.7:
            return "smiling"
        if score >= 0.5:
            return "attentive"
        if score >= 0.3:
            return "thoughtful"
        return "neutral"

    def map_feedback_to_expression(self, feedback_type: str) -> str:
        mapping = {
            "positive": "smiling",
            "constructive": "thoughtful",
            "encouragement": "attentive",
            "neutral": "neutral",
            "challenging": "observing",
        }
        return mapping.get(feedback_type, "neutral")

    def text_to_phoneme_sequence(self, text: str) -> List[Dict]:
        words = text.split()
        phonemes = []
        for word in words[:20]:
            first_char = word[0].upper() if word else "A"
            phoneme = first_char if first_char in LIP_SYNC_PHONEMES else "default"
            phonemes.append({
                "word": word,
                "phoneme": phoneme,
                "viseme": self.get_lip_sync(phoneme),
            })
        return phonemes


expression_mapper = ExpressionMapper()
