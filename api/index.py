from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from summarizer_agent.agent import (
    classify_text,
    context_answer_support,
    extractive_hint,
    root_agent,
)

# Prototype-only default env setup for hackathon deployment convenience.
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
os.environ.setdefault("GOOGLE_API_KEY", "AIzaSyAXDJb4dlkiltPy1HUspiBnye4U2V1nlIo")

app = FastAPI(title="ADK Multi-Agent API", version="1.0.0")

_session_service = InMemorySessionService()
_runner = Runner(
    app_name="summarizer_agent",
    agent=root_agent,
    session_service=_session_service,
    auto_create_session=True,
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    user_id: str = Field(default="vercel_user")
    session_id: str = Field(default="default_session")


class ChatResponse(BaseModel):
    response: str
    event_count: int
    app_name: str


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/chat")
async def chat_get(message: str | None = Query(default=None, description="Optional quick test prompt")) -> Dict[str, str]:
    if not message:
        return {
            "status": "ok",
            "usage": "Use POST /api/chat with JSON body: {\"message\":\"your prompt\"}",
        }

    result = await chat(ChatRequest(message=message))
    return {
        "response": result.response,
        "app_name": result.app_name,
    }


@app.api_route("/api/chat", methods=["PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def chat_method_fallback(request: Request) -> Dict[str, str]:
    return {
        "status": "ok",
        "method": request.method,
        "usage": "Use GET /api/chat for quick test or POST /api/chat with JSON body {\"message\":\"your prompt\"}",
    }


def _extract_text_from_events(events: List[Any]) -> str:
    for event in reversed(events):
        content = getattr(event, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None) or []
        chunks: List[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                chunks.append(text)
        if chunks:
            return "\n".join(chunks).strip()
    return ""


def _fallback_response(message: str) -> str:
    lower = message.lower().strip()

    if "classify" in lower:
        result = classify_text(message)
        return (
            "Prototype fallback (Gemini quota reached). "
            f"Topic: {result.get('predicted_topic', 'general')}; "
            f"Sentiment: {result.get('sentiment', 'neutral')}."
        )

    context_match = re.search(r"using this context:\s*(.*?)\s*question:\s*(.*)", message, re.IGNORECASE | re.DOTALL)
    if context_match:
        context = context_match.group(1).strip()
        question = context_match.group(2).strip()
        support = context_answer_support(context=context, question=question)
        sentences = support.get("supporting_sentences", [])
        if isinstance(sentences, list) and sentences:
            return (
                "Prototype fallback (Gemini quota reached). "
                f"Best grounded answer from context: {sentences[0]}"
            )

    if "summarize" in lower or "summary" in lower:
        text_to_summarize = message.split(":", 1)[-1].strip() if ":" in message else message
        summary_hint = extractive_hint(text=text_to_summarize, max_sentences=3)
        bullets = summary_hint.get("key_points", [])
        if isinstance(bullets, list) and bullets:
            bullet_text = " | ".join(str(x) for x in bullets[:3])
            return f"Prototype fallback (Gemini quota reached). Key points: {bullet_text}"

    return (
        "Prototype fallback (Gemini quota reached). "
        "Try a classify, summarize, or context-question prompt."
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    try:
        collected_events = await _runner.run_debug(
            user_messages=[payload.message],
            user_id=payload.user_id,
            session_id=payload.session_id,
        )
    except Exception as exc:  # pragma: no cover
        return ChatResponse(
            response=_fallback_response(payload.message),
            event_count=0,
            app_name="summarizer_agent",
        )

    text = _extract_text_from_events(collected_events)
    if not text:
        return ChatResponse(
            response=_fallback_response(payload.message),
            event_count=0,
            app_name="summarizer_agent",
        )

    return ChatResponse(
        response=text,
        event_count=len(collected_events),
        app_name="summarizer_agent",
    )
