# LLM / AI Application Patterns — Enterprise Standard

**Applies to:** Python projects building on top of LLMs (OpenAI, Anthropic, Gemini, local models).
**Sources:** awesome-cursorrules ML/LLM workflow rules + production LLM app experience.

---

## SECTION 1 — PROJECT STRUCTURE FOR LLM APPLICATIONS

```
my-llm-app/
├── app/
│   ├── prompts/                    ← prompt templates — version controlled, not inline
│   │   ├── __init__.py
│   │   ├── base.py                 ← PromptTemplate base class
│   │   ├── summarisation.py
│   │   ├── extraction.py
│   │   └── classification.py
│   ├── llm/                        ← LLM client wrappers and provider abstractions
│   │   ├── __init__.py
│   │   ├── base.py                 ← abstract LLMClient protocol
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   └── factory.py              ← creates correct client from config
│   ├── context/                    ← conversation and context management
│   │   ├── __init__.py
│   │   ├── conversation.py         ← conversation history with deque
│   │   └── retriever.py            ← RAG context retrieval
│   └── pipelines/                  ← orchestrated multi-step LLM workflows
│       ├── summarise_pipeline.py
│       └── extract_pipeline.py
```

---

## SECTION 2 — PROMPT MANAGEMENT

Prompts are code. Version-control them like code. Never inline them as f-strings scattered through business logic.

```python
# app/prompts/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from string import Template


@dataclass
class RenderedPrompt:
    """The output of rendering a prompt template with specific inputs."""
    system: str
    user: str
    version: str


class PromptTemplate(ABC):
    """Base for all prompt templates.

    Subclasses define the template and render() populates it with inputs.
    Version field enables A/B testing and rollback tracking.
    """
    version: str = "1.0.0"

    @abstractmethod
    def render(self, **kwargs: object) -> RenderedPrompt:
        """Render the template with provided inputs.

        Args:
            **kwargs: Template-specific inputs. Each subclass documents its own.

        Returns:
            RenderedPrompt with system and user content.
        """
        ...


# app/prompts/summarisation.py

class SummarisationPrompt(PromptTemplate):
    """Prompt for document summarisation.

    Version history:
        1.0.0 — initial
        1.1.0 — added language constraint
        1.2.0 — added length control
    """
    version = "1.2.0"

    _SYSTEM = (
        "You are a professional document summariser. "
        "Always respond in {language}. "
        "Never include information not present in the source document."
    )

    _USER = (
        "Summarise the following document in {max_sentences} sentences or fewer.\n\n"
        "DOCUMENT:\n{document}"
    )

    def render(
        self,
        *,
        document: str,
        max_sentences: int = 5,
        language: str = "English",
    ) -> RenderedPrompt:
        return RenderedPrompt(
            system=self._SYSTEM.format(language=language),
            user=self._USER.format(document=document, max_sentences=max_sentences),
            version=self.version,
        )
```

---

## SECTION 3 — LLM CLIENT ABSTRACTION

Never call LLM provider SDKs directly in business code. Wrap them behind a protocol so providers are swappable.

```python
# app/llm/base.py

from typing import Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for all LLM provider clients.

    All implementations must be async and must return LLMResponse.
    Callers depend on this protocol, never on a concrete provider.
    """

    async def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse: ...


# app/llm/anthropic_client.py

import anthropic
from app.llm.base import LLMClient, LLMResponse
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class AnthropicClient:
    """Anthropic Claude client implementing LLMClient protocol."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._default_model = settings.anthropic_model

    async def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        logger.debug(
            "llm_request_started",
            provider="anthropic",
            model=self._default_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = await self._client.messages.create(
            model=self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason or "unknown",
        )
```

---

## SECTION 4 — CONTEXT AND CONVERSATION MANAGEMENT

```python
# app/context/conversation.py

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str    # "user" or "assistant"
    content: str


class ConversationHistory:
    """Manages conversation context with a bounded history window.

    Uses deque with maxlen to automatically evict oldest messages
    when the window fills, preventing unbounded context growth.

    Args:
        max_turns: Maximum number of complete turns (user + assistant) to retain.
            Each turn = 2 messages. Default 10 = 20 messages max.
    """

    def __init__(self, max_turns: int = 10) -> None:
        self._messages: deque[Message] = deque(maxlen=max_turns * 2)

    def add_user_message(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))

    def to_api_format(self) -> list[dict[str, str]]:
        """Convert to the messages array format expected by most LLM APIs."""
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def clear(self) -> None:
        self._messages.clear()

    @property
    def turn_count(self) -> int:
        return len(self._messages) // 2
```

---

## SECTION 5 — STRUCTURED OUTPUT / JSON EXTRACTION

Always use Pydantic for LLM output parsing. Never manually parse LLM JSON strings.

```python
from pydantic import BaseModel, ValidationError
import json

class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    confidence: float
    context: str | None = None


async def extract_entities(
    text: str,
    llm: LLMClient,
) -> list[ExtractedEntity]:
    """Extract named entities from text using LLM with structured output.

    Args:
        text: Source text to extract entities from.
        llm: LLM client implementing the LLMClient protocol.

    Returns:
        List of validated ExtractedEntity objects.

    Raises:
        ExternalServiceError: If LLM call fails or returns unparseable output.
    """
    prompt = EntityExtractionPrompt().render(text=text)
    response = await llm.complete(
        system=prompt.system,
        user=prompt.user,
        temperature=0.0,    # deterministic for extraction tasks
    )

    try:
        raw = json.loads(response.content)
        return [ExtractedEntity.model_validate(entity) for entity in raw["entities"]]
    except (json.JSONDecodeError, KeyError, ValidationError) as exc:
        logger.error(
            "llm_parse_failed",
            provider_model=response.model,
            finish_reason=response.finish_reason,
            error=str(exc),
        )
        raise ExternalServiceError("llm", f"Failed to parse structured output: {exc}") from exc
```

---

## SECTION 6 — COST AND RATE LIMIT MANAGEMENT

```python
# Track token usage per request for cost monitoring
import structlog

logger = structlog.get_logger(__name__)


async def complete_with_tracking(
    llm: LLMClient,
    system: str,
    user: str,
    *,
    operation: str,
    tenant_id: int,
) -> LLMResponse:
    """Call LLM and log token usage for cost tracking.

    All LLM calls in production MUST go through this wrapper.
    Token counts feed into per-tenant cost monitoring dashboards.
    """
    response = await llm.complete(system=system, user=user)

    logger.info(
        "llm_call_completed",
        operation=operation,
        tenant_id=tenant_id,
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.prompt_tokens + response.completion_tokens,
        finish_reason=response.finish_reason,
    )

    return response


# Rate limiting LLM calls per tenant (using Redis token bucket)
async def check_llm_quota(tenant_id: int, redis: Redis) -> None:
    """Enforce per-tenant LLM call rate limit.

    Raises RateLimitError if tenant has exceeded their allocated calls.
    """
    key = f"llm:quota:{tenant_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 3600)   # 1-hour window
    if count > settings.llm_calls_per_tenant_per_hour:
        raise RateLimitError(retry_after_seconds=3600)
```
