from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import deque
import time


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


class ConversationMemory:
    def __init__(self, max_turns: int = 10, max_tokens: int = 4000):
        self._turns: deque = deque(maxlen=max_turns)
        self._max_turns = max_turns
        self._max_tokens = max_tokens
        self._topic: str = ""
        self._mode: str = ""
        self._session_start: float = time.time()
        self._turn_count: int = 0

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def session_duration(self) -> float:
        return time.time() - self._session_start

    @property
    def topic(self) -> str:
        return self._topic

    @topic.setter
    def topic(self, value: str) -> None:
        self._topic = value

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode = value

    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        self._turns.append(
            ConversationTurn(
                role="user",
                content=content,
                metadata=metadata or {},
            )
        )
        self._turn_count += 1

    def add_ai_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        self._turns.append(
            ConversationTurn(
                role="assistant",
                content=content,
                metadata=metadata or {},
            )
        )

    def get_history(self, include_metadata: bool = False) -> List[Dict]:
        if include_metadata:
            return [
                {"role": t.role, "content": t.content, "metadata": t.metadata}
                for t in self._turns
            ]
        return [
            {"role": t.role, "content": t.content}
            for t in self._turns
        ]

    def get_last_user_message(self) -> Optional[str]:
        for turn in reversed(self._turns):
            if turn.role == "user":
                return turn.content
        return None

    def get_last_ai_message(self) -> Optional[str]:
        for turn in reversed(self._turns):
            if turn.role == "assistant":
                return turn.content
        return None

    def get_recent_exchanges(self, n: int = 3) -> List[Dict]:
        recent = list(self._turns)[-n * 2:]
        return [
            {"role": t.role, "content": t.content}
            for t in recent
        ]

    def format_for_llm(self, system_prompt: str) -> List[Dict]:
        messages = [{"role": "system", "content": system_prompt}]
        if self._topic:
            messages.append({
                "role": "system",
                "content": f"The current conversation topic is: {self._topic}"
            })
        messages.extend(self.get_history())
        return messages

    def clear(self) -> None:
        self._turns.clear()
        self._turn_count = 0
        self._session_start = time.time()

    def estimate_token_count(self) -> int:
        total = 0
        for turn in self._turns:
            total += len(turn.content.split()) * 1.3
        return int(total)
