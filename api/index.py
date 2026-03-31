from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
        return """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>ADK Multi-Agent Prototype</title>
    <style>
        :root {
            --bg: #f8f7f4;
            --ink: #1f2430;
            --muted: #5f6b7a;
            --accent: #0b6e4f;
            --accent-2: #f4a259;
            --card: #ffffff;
            --border: #d8dde6;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Georgia, Cambria, \"Times New Roman\", serif;
            background:
                radial-gradient(circle at 20% 20%, #efe8dc 0%, transparent 40%),
                radial-gradient(circle at 80% 0%, #e2f0ea 0%, transparent 35%),
                var(--bg);
            color: var(--ink);
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .shell {
            width: min(920px, 100%);
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: 0 18px 60px rgba(29, 42, 68, 0.12);
            overflow: hidden;
        }
        .hero {
            padding: 20px 22px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(135deg, #fffdf8 0%, #f4fbf8 100%);
        }
        .title {
            margin: 0;
            font-size: clamp(24px, 3vw, 34px);
            line-height: 1.1;
        }
        .sub {
            margin: 8px 0 0;
            color: var(--muted);
            font-size: 15px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 14px;
            padding: 18px 22px 22px;
        }
        textarea {
            width: 100%;
            min-height: 120px;
            resize: vertical;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            font: 15px/1.4 \"Segoe UI\", Tahoma, sans-serif;
        }
        .row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button {
            border: 0;
            border-radius: 10px;
            background: var(--accent);
            color: white;
            padding: 10px 14px;
            font: 600 14px/1 \"Segoe UI\", Tahoma, sans-serif;
            cursor: pointer;
        }
        button.alt {
            background: var(--accent-2);
            color: #222;
        }
        .out {
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 12px;
            min-height: 120px;
            white-space: pre-wrap;
            font: 14px/1.45 \"Consolas\", \"Courier New\", monospace;
            background: #fcfcfc;
        }
        .meta {
            color: var(--muted);
            font: 13px/1.3 \"Segoe UI\", Tahoma, sans-serif;
        }
        .hint {
            color: var(--muted);
            font-size: 12px;
        }
    </style>
</head>
<body>
    <main class=\"shell\">
        <section class=\"hero\">
            <h1 class=\"title\">ADK Multi-Agent Prototype</h1>
            <p class=\"sub\">Summarization, classification, and grounded Q&A in one endpoint.</p>
        </section>
        <section class=\"grid\">
            <label for=\"prompt\" class=\"meta\">Prompt</label>
            <textarea id=\"prompt\">Summarize: Cloud Run scales stateless containers and charges by usage.</textarea>
            <div class=\"row\">
                <button id=\"runBtn\">Run Agent</button>
                <button id=\"sample1\" class=\"alt\">Sample: Classify</button>
                <button id=\"sample2\" class=\"alt\">Sample: Grounded Q&A</button>
            </div>
            <div id=\"status\" class=\"meta\">Ready</div>
            <div id=\"out\" class=\"out\">Response will appear here.</div>
            <div class=\"hint\">API routes: /api/chat, /api/health</div>
        </section>
    </main>

    <script>
        const promptEl = document.getElementById('prompt');
        const outEl = document.getElementById('out');
        const statusEl = document.getElementById('status');
        const runBtn = document.getElementById('runBtn');

        async function runPrompt() {
            const message = promptEl.value.trim();
            if (!message) {
                statusEl.textContent = 'Please enter a prompt.';
                return;
            }
            runBtn.disabled = true;
            statusEl.textContent = 'Running...';
            outEl.textContent = '';
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const data = await res.json();
                if (!res.ok) {
                    outEl.textContent = JSON.stringify(data, null, 2);
                    statusEl.textContent = `Error ${res.status}`;
                    return;
                }
                outEl.textContent = data.response || JSON.stringify(data, null, 2);
                statusEl.textContent = `Done (${res.status})`;
            } catch (err) {
                outEl.textContent = String(err);
                statusEl.textContent = 'Network error';
            } finally {
                runBtn.disabled = false;
            }
        }

        runBtn.addEventListener('click', runPrompt);
        document.getElementById('sample1').addEventListener('click', () => {
            promptEl.value = 'Classify this text by topic and sentiment: I love the camera quality but battery drains fast.';
        });
        document.getElementById('sample2').addEventListener('click', () => {
            promptEl.value = 'Using this context: Cloud Run automatically scales stateless containers and charges by usage. Question: Why is Cloud Run cost efficient?';
        });
    </script>
</body>
</html>
"""


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
