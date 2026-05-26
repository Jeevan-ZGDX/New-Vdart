from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("languages")


LANGUAGE_DEFINITIONS = {
    "en": {
        "name": "English",
        "native_name": "English",
        "code": "en",
        "whisper_code": "en",
        "tts_code": "en",
        "accent_variants": ["us", "uk", "au", "in"],
        "difficulty": "beginner",
        "grammar_rules": "english",
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "code": "hi",
        "whisper_code": "hi",
        "tts_code": "hi",
        "accent_variants": ["in"],
        "difficulty": "moderate",
        "grammar_rules": "hindi",
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "code": "ta",
        "whisper_code": "ta",
        "tts_code": "ta",
        "accent_variants": ["in", "lk"],
        "difficulty": "moderate",
        "grammar_rules": "tamil",
    },
    "es": {
        "name": "Spanish",
        "native_name": "Español",
        "code": "es",
        "whisper_code": "es",
        "tts_code": "es",
        "accent_variants": ["es", "mx", "ar"],
        "difficulty": "moderate",
        "grammar_rules": "spanish",
    },
    "fr": {
        "name": "French",
        "native_name": "Français",
        "code": "fr",
        "whisper_code": "fr",
        "tts_code": "fr",
        "accent_variants": ["fr", "ca"],
        "difficulty": "moderate",
        "grammar_rules": "french",
    },
}


COMMON_PHRASES = {
    "en": {
        "greeting": "Hello! Let's practice your communication skills.",
        "feedback_positive": "Great improvement!",
        "feedback_constructive": "Try to speak more slowly and clearly.",
        "encouragement": "You're doing well! Keep practicing.",
    },
    "hi": {
        "greeting": "नमस्ते! आइए आपके संचार कौशल का अभ्यास करें।",
        "feedback_positive": "बहुत अच्छा सुधार!",
        "feedback_constructive": "धीरे और स्पष्ट बोलने की कोशिश करें।",
        "encouragement": "आप अच्छा कर रहे हैं! अभ्यास जारी रखें।",
    },
    "ta": {
        "greeting": "வணக்கம்! உங்கள் தகவல் தொடர்பு திறன்களை பயிற்சி செய்வோம்.",
        "feedback_positive": "சிறந்த முன்னேற்றம்!",
        "feedback_constructive": "மெதுவாக மற்றும் தெளிவாக பேச முயற்சிக்கவும்.",
        "encouragement": "நீங்கள் நன்றாக செய்கிறீர்கள்! தொடர்ந்து பயிற்சி செய்யுங்கள்.",
    },
    "es": {
        "greeting": "¡Hola! Practiquemos tus habilidades de comunicación.",
        "feedback_positive": "¡Gran mejora!",
        "feedback_constructive": "Intenta hablar más lento y claro.",
        "encouragement": "¡Lo estás haciendo bien! Sigue practicando.",
    },
    "fr": {
        "greeting": "Bonjour ! Pratiquons vos compétences en communication.",
        "feedback_positive": "Grande amélioration !",
        "feedback_constructive": "Essayez de parler plus lentement et clairement.",
        "encouragement": "Vous faites du bon travail ! Continuez à pratiquer.",
    },
}


class LanguageManager:
    def get_supported_languages(self) -> List[Dict]:
        return [
            {
                "code": code,
                "name": lang["name"],
                "native_name": lang["native_name"],
                "difficulty": lang["difficulty"],
            }
            for code, lang in LANGUAGE_DEFINITIONS.items()
        ]

    def get_language(self, code: str) -> Optional[Dict]:
        return LANGUAGE_DEFINITIONS.get(code)

    def get_phrase(self, lang_code: str, phrase_key: str) -> str:
        lang_phrases = COMMON_PHRASES.get(lang_code, COMMON_PHRASES["en"])
        return lang_phrases.get(phrase_key, COMMON_PHRASES["en"].get(phrase_key, ""))

    def get_accent_variants(self, lang_code: str) -> List[str]:
        lang = self.get_language(lang_code)
        return lang.get("accent_variants", []) if lang else []

    def estimate_difficulty(self, lang_code: str, native_lang: str) -> str:
        if lang_code == native_lang:
            return "beginner"
        lang_pairs = {
            ("en", "hi"): "moderate",
            ("en", "ta"): "moderate",
            ("en", "es"): "easy",
            ("en", "fr"): "easy",
            ("hi", "en"): "moderate",
            ("ta", "en"): "moderate",
            ("es", "en"): "easy",
            ("fr", "en"): "easy",
        }
        return lang_pairs.get((lang_code, native_lang), "moderate")


language_manager = LanguageManager()
