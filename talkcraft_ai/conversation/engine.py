import time
from typing import Optional, Callable, Dict, List

from talkcraft_ai.agents.llm_client import LLMClient
from talkcraft_ai.agents.response_generator import ResponseGenerator, GeneratedResponse
from talkcraft_ai.agents.followup_generator import FollowUpGenerator
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.conversation.modes import get_mode, get_topics_for_mode
from talkcraft_ai.conversation.difficulty import DifficultyAdapter
from talkcraft_ai.scoring.conversation_scorer import ConversationScorer
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("conversation_engine")


class ConversationEngine:
    def __init__(self, llm_client: LLMClient, scorer: ConversationScorer):
        self._llm = llm_client
        self._scorer = scorer
        self._response_generator = ResponseGenerator(llm_client)
        self._followup_generator = FollowUpGenerator(llm_client)
        self._memory = ConversationMemory()
        self._difficulty = DifficultyAdapter()
        self._mode_id: str = "casual_conversation"
        self._topic: str = ""
        self._active: bool = False
        self._current_ai_response: str = ""
        self._first_turn: bool = True
        self._utterance_accumulator: List[str] = []
        self._last_utterance_time: float = 0.0
        self._on_mode_change: Optional[Callable[[str], None]] = None
        self._on_difficulty_change: Optional[Callable[[str, str], None]] = None
        self._on_conversation_end: Optional[Callable[[Dict], None]] = None
        self._greeting_cache: Dict[str, str] = {}

    @property
    def memory(self) -> ConversationMemory:
        return self._memory

    @property
    def difficulty(self) -> DifficultyAdapter:
        return self._difficulty

    @property
    def mode_id(self) -> str:
        return self._mode_id

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def is_active(self) -> bool:
        return self._active

    def set_mode(self, mode_id: str, topic: str = "") -> None:
        self._mode_id = mode_id
        self._memory.mode = mode_id
        self._topic = topic or ""
        self._memory.topic = self._topic
        if self._on_mode_change:
            self._on_mode_change(mode_id)
        logger.info(f"Mode set to {mode_id}", extra={"topic": topic})

    def set_callbacks(
        self,
        on_mode_change: Optional[Callable[[str], None]] = None,
        on_difficulty_change: Optional[Callable[[str, str], None]] = None,
        on_conversation_end: Optional[Callable[[Dict], None]] = None,
    ) -> None:
        self._on_mode_change = on_mode_change
        self._on_difficulty_change = on_difficulty_change
        self._on_conversation_end = on_conversation_end

    def start_conversation(self) -> Optional[GeneratedResponse]:
        if self._active:
            return None
        self._active = True
        self._first_turn = True
        self._memory.clear()
        self._difficulty.reset()
        self._scorer.reset()
        self._utterance_accumulator.clear()
        greeting = self._generate_greeting()
        if greeting:
            self._memory.add_ai_message(greeting)
        logger.info(f"Conversation started — mode={self._mode_id}, topic={self._topic or 'none'}")
        return GeneratedResponse(content=greeting) if greeting else None

    def stop_conversation(self) -> Dict:
        if not self._active:
            return {}
        self._active = False
        summary = self._generate_summary()
        if self._on_conversation_end:
            self._on_conversation_end(summary)
        logger.info(
            "Conversation ended",
            extra={"turns": self._memory.turn_count, "duration": f"{self._memory.session_duration:.1f}s"},
        )
        return summary

    def process_user_input(
        self,
        text: str,
        vision_data: Optional[Dict] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Optional[GeneratedResponse]:
        if not self._active or not text.strip():
            return None
        self._memory.add_user_message(text, metadata={"mode": self._mode_id})
        self._scorer.update_from_conversation(text, self._memory)
        if vision_data:
            self._scorer.update_from_vision(vision_data)
        response = self._response_generator.generate(
            self._memory,
            self._difficulty,
            on_chunk=on_chunk,
        )
        if response and response.content:
            self._memory.add_ai_message(response.content, metadata={"latency": response.latency})
            self._scorer.record_turn()
            filler_rate = self._scorer.current.filler
            difficulty_change = self._difficulty.update(
                grammar=self._scorer.current.grammar,
                filler=filler_rate,
                pace=self._scorer.current.pace,
                clarity=self._scorer.current.clarity,
                engagement=self._scorer.current.engagement,
            )
            if difficulty_change and self._on_difficulty_change:
                parts = difficulty_change.replace("difficulty_changed:", "").split("->")
                if len(parts) == 2:
                    self._on_difficulty_change(parts[0], parts[1])
        return response

    def accumulate_utterance(self, text: str) -> Optional[str]:
        now = time.time()
        self._utterance_accumulator.append(text)
        self._last_utterance_time = now
        return None

    def flush_utterance(self) -> Optional[str]:
        if not self._utterance_accumulator:
            return None
        full_text = " ".join(self._utterance_accumulator).strip()
        self._utterance_accumulator.clear()
        return full_text if full_text else None

    def generate_followup_questions(self, count: int = 3) -> List[str]:
        return self._followup_generator.generate(self._memory, count)

    def _generate_greeting(self) -> str:
        mode = get_mode(self._mode_id)
        cache_key = f"{self._mode_id}:{self._topic}"
        if cache_key in self._greeting_cache:
            return self._greeting_cache[cache_key]

        prompt = (
            f"You are in {mode.name} mode. "
            f"Topic: {self._topic or 'general conversation'}. "
            "Generate a brief, natural greeting (2-3 sentences) to start the conversation. "
            "Introduce the topic and invite the user to begin. Be warm and engaging. "
            "Do NOT mention you are an AI."
        )
        if self._topic:
            prompt += f"\nStart directly with the topic: {self._topic}"

        greeting = self._llm.generate([
            {"role": "system", "content": mode.system_prompt},
            {"role": "user", "content": prompt},
        ])
        result = greeting.content.strip()
        self._greeting_cache[cache_key] = result
        return result

    def _generate_summary(self) -> Dict:
        scores = self._scorer.get_scores_dict()
        return {
            "mode": self._mode_id,
            "topic": self._topic,
            "total_turns": self._memory.turn_count,
            "duration": round(self._memory.session_duration, 1),
            "scores": scores,
            "difficulty": self._difficulty.level,
        }
