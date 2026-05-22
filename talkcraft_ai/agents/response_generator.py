from typing import Optional, Callable, List, Dict
from dataclasses import dataclass, field

from talkcraft_ai.agents.llm_client import LLMClient, LLMResponse
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.conversation.modes import get_mode
from talkcraft_ai.conversation.difficulty import DifficultyAdapter
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("response_generator")


@dataclass
class GeneratedResponse:
    content: str
    finish_reason: str = ""
    latency: float = 0.0
    truncated: bool = False


class ResponseGenerator:
    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    def generate(
        self,
        memory: ConversationMemory,
        difficulty: DifficultyAdapter,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> GeneratedResponse:
        mode = get_mode(memory.mode)
        system_prompt = self._build_system_prompt(mode.system_prompt, difficulty)
        messages = memory.format_for_llm(system_prompt)
        logger.debug(
            "Generating response",
            extra={"mode": memory.mode, "difficulty": difficulty.level, "messages": len(messages)},
        )
        if self._llm.streaming:
            response = self._llm.generate_stream(messages, on_chunk=on_chunk)
        else:
            response = self._llm.generate(messages)
            if on_chunk:
                on_chunk(response.content)
        return GeneratedResponse(
            content=response.content,
            finish_reason=response.finish_reason,
            latency=response.latency,
            truncated=len(response.content.split()) > 200,
        )

    def _build_system_prompt(self, base_prompt: str, difficulty: DifficultyAdapter) -> str:
        difficulty_instruction = difficulty.get_difficulty_prompt_addition()
        return f"{base_prompt}\n\nDifficulty Level ({difficulty.level}):\n{difficulty_instruction}\n\nIMPORTANT RULES:\n- Keep responses concise (2-4 sentences maximum unless analyzing)\n- Never mention that you are an AI or language model\n- Stay in character as your assigned role\n- Respond naturally as a human would\n- If the user asks something off-topic, gently guide back to the conversation"
