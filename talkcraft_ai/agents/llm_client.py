import json
import time
from typing import Generator, List, Dict, Optional, Callable
from dataclasses import dataclass
import requests

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("llm_client")


@dataclass
class LLMResponse:
    content: str
    finish_reason: str = ""
    usage: Dict = None
    latency: float = 0.0


class LLMClient:
    def __init__(self):
        cfg = config.llm
        self.api_base = cfg.api_base.rstrip("/")
        self.api_key = cfg.api_key
        self.model = cfg.model
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens
        self.top_p = cfg.top_p
        self.frequency_penalty = cfg.frequency_penalty
        self.presence_penalty = cfg.presence_penalty
        self.timeout = cfg.timeout
        self.streaming = cfg.streaming
        self._session = requests.Session()
        logger.info(
            "LLMClient initialized",
            extra={
                "api_base": self.api_base,
                "model": self.model,
                "streaming": self.streaming,
            },
        )

    def _headers(self) -> Dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _payload(self, messages: List[Dict], stream: bool = False) -> Dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": stream,
        }

    def generate(self, messages: List[Dict]) -> LLMResponse:
        start = time.time()
        url = f"{self.api_base}/chat/completions"
        try:
            resp = self._session.post(
                url,
                headers=self._headers(),
                json=self._payload(messages, stream=False),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            latency = time.time() - start
            choice = data.get("choices", [{}])[0]
            usage = data.get("usage", {})
            logger.debug(
                "LLM response received",
                extra={"latency": f"{latency:.2f}s", "tokens": usage},
            )
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                finish_reason=choice.get("finish_reason", ""),
                usage=usage,
                latency=latency,
            )
        except requests.exceptions.Timeout:
            logger.error(f"LLM request timed out after {self.timeout}s")
            return LLMResponse(content="I apologize, but I'm having trouble processing that. Could you please repeat?")
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to LLM API at {url}")
            return LLMResponse(content="I seem to be having connection issues. Please check if the LLM service is running.")
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            return LLMResponse(content="I encountered an error. Let's continue — could you rephrase that?")
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            return LLMResponse(content="Let me try again. What would you like to discuss?")

    def generate_stream(
        self, messages: List[Dict], on_chunk: Optional[Callable[[str], None]] = None
    ) -> LLMResponse:
        start = time.time()
        url = f"{self.api_base}/chat/completions"
        collected_content = []
        try:
            resp = self._session.post(
                url,
                headers=self._headers(),
                json=self._payload(messages, stream=True),
                timeout=self.timeout,
                stream=True,
            )
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected_content.append(content)
                            if on_chunk:
                                on_chunk(content)
                    except json.JSONDecodeError:
                        continue
            latency = time.time() - start
            full_content = "".join(collected_content)
            logger.debug(
                "Streaming LLM response complete",
                extra={"latency": f"{latency:.2f}s", "length": len(full_content)},
            )
            return LLMResponse(
                content=full_content,
                finish_reason="stop",
                latency=latency,
            )
        except requests.exceptions.Timeout:
            logger.error(f"Streaming LLM request timed out after {self.timeout}s")
            fallback = "I apologize, but I'm having trouble processing that. Could you please repeat?"
            if on_chunk:
                on_chunk(fallback)
            return LLMResponse(content=fallback)
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to LLM API for streaming at {url}")
            fallback = "I seem to be having connection issues. Please check if the LLM service is running."
            if on_chunk:
                on_chunk(fallback)
            return LLMResponse(content=fallback)
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming LLM request failed: {e}")
            fallback = "I encountered an error. Let's continue — could you rephrase that?"
            if on_chunk:
                on_chunk(fallback)
            return LLMResponse(content=fallback)
        except Exception as e:
            logger.error(f"Unexpected streaming error: {e}")
            fallback = "Let me try again. What would you like to discuss?"
            if on_chunk:
                on_chunk(fallback)
            return LLMResponse(content=fallback)

    def is_available(self) -> bool:
        try:
            url = f"{self.api_base}/models"
            resp = self._session.get(
                url,
                headers=self._headers(),
                timeout=5.0,
            )
            return resp.status_code == 200
        except Exception:
            return False
