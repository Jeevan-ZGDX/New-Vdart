import time
import re
from typing import Optional, Dict, Any, List
from threading import Lock

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


class GrammarChecker:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._tool = None
        self._logger = get_logger("talkcraft.analysis.grammar")
        self._loaded = False
        self._total_errors = 0
        self._initialized = True
        self._cache = {}

    def load(self):
        if self._loaded:
            return

        self._logger.info("Loading LanguageTool grammar checker...")
        start = time.time()

        try:
            import language_tool_python

            self._tool = language_tool_python.LanguageTool(
                config.analysis.grammar_language,
                config={"cacheSize": 100, "pipelineCaching": True},
            )
            self._loaded = True
            self._logger.info(f"LanguageTool loaded in {time.time() - start:.2f}s")
        except ImportError:
            self._logger.warning(
                "language_tool_python not installed. "
                "Grammar checking will use fallback."
            )
            self._loaded = False
        except Exception as e:
            self._logger.warning(f"Failed to load LanguageTool: {e}")
            self._loaded = False

    def check(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or len(text.strip()) < 3:
            return None

        cache_key = text.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        start = time.time()

        if self._loaded and self._tool:
            try:
                matches = self._tool.check(text)
                error_count = len(matches)

                error_types = {}
                for match in matches:
                    rule_id = match.ruleId
                    error_types[rule_id] = error_types.get(rule_id, 0) + 1

                suggestions = []
                for match in matches[:5]:
                    if match.replacements:
                        suggestions.append({
                            "message": match.message,
                            "replacements": match.replacements[:3],
                            "context": match.context,
                        })

                result = {
                    "error_count": error_count,
                    "error_types": error_types,
                    "suggestions": suggestions,
                    "processing_time": time.time() - start,
                }

                self._total_errors += error_count

            except Exception as e:
                self._logger.error(f"Grammar check error: {e}")
                result = self._fallback_check(text)
        else:
            result = self._fallback_check(text)

        self._cache[cache_key] = result
        if len(self._cache) > 500:
            self._cache.clear()

        return result

    def _fallback_check(self, text: str) -> Dict[str, Any]:
        common_errors = [
            (r"\b(their|there|they're)\b", "their/there/they're confusion"),
            (r"\b(your|you're)\b", "your/you're confusion"),
            (r"\b(its|it's)\b", "its/it's confusion"),
            (r"\b(to|too|two)\b", "to/too/two confusion"),
            (r"\b(effect|affect)\b", "effect/affect confusion"),
        ]

        error_count = 0
        error_types = {}

        for pattern, description in common_errors:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                error_count += len(matches)
                error_types[description] = len(matches)

        result = {
            "error_count": error_count,
            "error_types": error_types,
            "suggestions": [],
            "processing_time": 0.0,
        }

        return result

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def unload(self):
        if self._tool:
            try:
                self._tool.close()
            except Exception:
                pass
            self._tool = None
            self._loaded = False
