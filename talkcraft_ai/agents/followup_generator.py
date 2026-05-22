from typing import List, Optional, Dict

from talkcraft_ai.agents.llm_client import LLMClient, LLMResponse
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("followup_generator")


class FollowUpGenerator:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    def generate(self, memory: ConversationMemory, count: int = 3) -> List[str]:
        recent = memory.get_recent_exchanges(n=2)
        if not recent:
            return []
        context = self._format_context(recent)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a conversation analyst. Based on the recent conversation exchange, "
                    "generate relevant follow-up questions that would help deepen the conversation. "
                    f"Return exactly {count} questions, one per line, numbered 1-{count}. "
                    "Make questions natural and conversational."
                ),
            },
            {
                "role": "user",
                "content": f"Recent conversation:\n{context}\n\nGenerate {count} follow-up questions:",
            },
        ]
        try:
            response = self._llm.generate(messages)
            questions = self._parse_questions(response.content, count)
            logger.debug(f"Generated {len(questions)} follow-up questions")
            return questions
        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return []

    def _format_context(self, exchanges: List[Dict]) -> str:
        lines = []
        for ex in exchanges:
            role = ex.get("role", "unknown")
            content = ex.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_questions(self, text: str, count: int) -> List[str]:
        questions = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            cleaned = line.lstrip("0123456789. )-–—").strip()
            if cleaned and (cleaned.endswith("?") or len(cleaned) > 10):
                questions.append(cleaned)
        return questions[:count]

    def is_relevant(self, user_message: str, topic: str) -> bool:
        if not topic:
            return True
        keywords = topic.lower().split()
        message_lower = user_message.lower()
        return any(kw in message_lower for kw in keywords)
