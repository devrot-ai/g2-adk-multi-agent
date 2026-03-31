from __future__ import annotations

import io
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
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


class LearningRequest(BaseModel):
    text: str = Field(..., min_length=1)
    title: Optional[str] = None


class LearningScene(BaseModel):
    scene_number: int
    heading: str
    narration: str
    visual_hint: str


class LearningResponse(BaseModel):
    title: str
    short_summary: str
    estimated_duration_sec: int
    scenes: List[LearningScene]


class UploadSummaryResponse(BaseModel):
    filename: str
    characters: int
    response: str
    app_name: str
    event_count: int
    learning_pack: LearningResponse


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
        .card {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            background: #fff;
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
        .scenes {
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 10px;
            min-height: 80px;
            background: #fcfcfc;
            font: 14px/1.45 "Segoe UI", Tahoma, sans-serif;
        }
        .scene-item {
            padding: 8px;
            border-left: 3px solid var(--accent-2);
            margin: 6px 0;
            background: #fff8f0;
        }
    </style>
</head>
<body>
    <main class=\"shell\">
        <section class=\"hero\">
            <h1 class=\"title\">ADK Multi-Agent Prototype</h1>
            <p class=\"sub\">Summarization, classification, grounded Q&A, document upload, and learning mode.</p>
        </section>
        <section class=\"grid\">
            <div class=\"card\">
                <label for=\"docFile\" class=\"meta\">Upload document (.txt, .md, .pdf, .docx)</label>
                <div class=\"row\" style=\"margin-top:8px\">
                    <input id=\"docFile\" type=\"file\" accept=\".txt,.md,.pdf,.docx\" />
                    <button id=\"uploadBtn\" class=\"alt\">Upload & Summarize</button>
                </div>
            </div>

            <label for=\"prompt\" class=\"meta\">Prompt</label>
            <textarea id=\"prompt\">Summarize: Cloud Run scales stateless containers and charges by usage.</textarea>
            <div class=\"row\">
                <button id=\"runBtn\">Run Agent</button>
                <button id=\"sample1\" class=\"alt\">Sample: Classify</button>
                <button id=\"sample2\" class=\"alt\">Sample: Grounded Q&A</button>
                <button id=\"learnBtn\" class=\"alt\">Create Learning Video</button>
                <button id=\"playBtn\" class=\"alt\">Play Narration</button>
            </div>
            <div id=\"status\" class=\"meta\">Ready</div>
            <div id=\"out\" class=\"out\">Response will appear here.</div>
            <div id=\"scenes\" class=\"scenes\">Learning scenes will appear here.</div>
            <div class=\"hint\">API routes: /api/chat, /api/health</div>
        </section>
    </main>

    <script>
        const promptEl = document.getElementById('prompt');
        const outEl = document.getElementById('out');
        const scenesEl = document.getElementById('scenes');
        const statusEl = document.getElementById('status');
        const runBtn = document.getElementById('runBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        let learningPack = null;

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

        async function uploadAndSummarize() {
            const input = document.getElementById('docFile');
            if (!input.files || input.files.length === 0) {
                statusEl.textContent = 'Choose a file first.';
                return;
            }
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);

            uploadBtn.disabled = true;
            statusEl.textContent = `Uploading ${file.name}...`;
            outEl.textContent = '';
            try {
                const res = await fetch('/api/upload-summarize', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (!res.ok) {
                    outEl.textContent = JSON.stringify(data, null, 2);
                    statusEl.textContent = `Upload failed (${res.status})`;
                    return;
                }
                outEl.textContent = data.response;
                learningPack = data.learning_pack;
                renderScenes(learningPack);
                statusEl.textContent = `Document summarized (${res.status})`;
            } catch (err) {
                outEl.textContent = String(err);
                statusEl.textContent = 'Upload error';
            } finally {
                uploadBtn.disabled = false;
            }
        }

        function renderScenes(pack) {
            if (!pack || !Array.isArray(pack.scenes)) {
                scenesEl.textContent = 'No learning scenes available yet.';
                return;
            }
            scenesEl.innerHTML = '';
            pack.scenes.forEach((s) => {
                const div = document.createElement('div');
                div.className = 'scene-item';
                div.innerHTML = `<strong>Scene ${s.scene_number}: ${s.heading}</strong><br>${s.narration}`;
                scenesEl.appendChild(div);
            });
        }

        async function buildLearningPack() {
            const text = promptEl.value.trim();
            if (!text) {
                statusEl.textContent = 'Enter prompt text first.';
                return;
            }
            statusEl.textContent = 'Creating learning pack...';
            try {
                const res = await fetch('/api/learning-pack', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, title: 'Learning Pack' })
                });
                const data = await res.json();
                if (!res.ok) {
                    outEl.textContent = JSON.stringify(data, null, 2);
                    statusEl.textContent = `Learning pack failed (${res.status})`;
                    return;
                }
                learningPack = data;
                renderScenes(data);
                outEl.textContent = `${data.short_summary}\n\nEstimated duration: ${data.estimated_duration_sec}s`;
                statusEl.textContent = `Learning pack ready (${res.status})`;
            } catch (err) {
                outEl.textContent = String(err);
                statusEl.textContent = 'Learning pack error';
            }
        }

        function speak(text) {
            return new Promise((resolve) => {
                if (!('speechSynthesis' in window)) {
                    resolve();
                    return;
                }
                const utter = new SpeechSynthesisUtterance(text);
                utter.rate = 1;
                utter.pitch = 1;
                utter.onend = () => resolve();
                utter.onerror = () => resolve();
                window.speechSynthesis.speak(utter);
            });
        }

        async function playLearningMode() {
            if (!learningPack || !Array.isArray(learningPack.scenes) || learningPack.scenes.length === 0) {
                statusEl.textContent = 'Create a learning pack first.';
                return;
            }
            statusEl.textContent = 'Playing learning narration...';
            for (const scene of learningPack.scenes) {
                outEl.textContent = `Scene ${scene.scene_number}: ${scene.heading}\n\n${scene.narration}`;
                await speak(`Scene ${scene.scene_number}. ${scene.heading}. ${scene.narration}`);
            }
            statusEl.textContent = 'Narration complete.';
        }

        runBtn.addEventListener('click', runPrompt);
        uploadBtn.addEventListener('click', uploadAndSummarize);
        document.getElementById('learnBtn').addEventListener('click', buildLearningPack);
        document.getElementById('playBtn').addEventListener('click', playLearningMode);
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


def _normalize_text(text: str, max_chars: int = 18000) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "\n\n[Truncated for prototype processing.]"


async def _extract_document_text(file: UploadFile) -> str:
    raw = await file.read()
    if not raw:
        return ""

    suffix = Path(file.filename or "").suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".py", ".log"}:
        return raw.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception:
            return ""
        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages[:30]]
        return "\n".join(pages)

    if suffix == ".docx":
        try:
            from docx import Document
        except Exception:
            return ""
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)

    return raw.decode("utf-8", errors="ignore")


def _build_learning_pack(text: str, title: Optional[str] = None) -> LearningResponse:
    clipped = _normalize_text(text, max_chars=6000)
    hints = extractive_hint(clipped, max_sentences=4)
    points = hints.get("key_points", []) if isinstance(hints, dict) else []
    if not isinstance(points, list) or not points:
        points = [clipped[:260]]

    scenes: List[LearningScene] = []
    for idx, point in enumerate(points[:4], start=1):
        content = str(point)
        scenes.append(
            LearningScene(
                scene_number=idx,
                heading=f"Key Idea {idx}",
                narration=content,
                visual_hint=f"Show slide {idx} with one key takeaway and an icon.",
            )
        )

    short_summary = " ".join(str(x) for x in points[:2])
    return LearningResponse(
        title=title or "Learning Video Pack",
        short_summary=short_summary,
        estimated_duration_sec=max(20, len(scenes) * 14),
        scenes=scenes,
    )


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


@app.post("/api/learning-pack", response_model=LearningResponse)
async def learning_pack(payload: LearningRequest) -> LearningResponse:
    return _build_learning_pack(payload.text, title=payload.title)


@app.post("/api/upload-summarize", response_model=UploadSummaryResponse)
async def upload_summarize(
    file: UploadFile = File(...),
    user_id: str = Form("vercel_user"),
    session_id: str = Form("upload_session"),
) -> UploadSummaryResponse:
    extracted = await _extract_document_text(file)
    extracted = _normalize_text(extracted)

    if not extracted.strip():
        extracted = "Could not extract text from this document."

    prompt = (
        "Summarize this document for learning. Return 4 bullets and one line called Core takeaway.\n\n"
        f"Document:\n{extracted}"
    )
    chat_result = await chat(ChatRequest(message=prompt, user_id=user_id, session_id=session_id))
    pack = _build_learning_pack(extracted, title=file.filename or "Uploaded document")

    return UploadSummaryResponse(
        filename=file.filename or "uploaded_file",
        characters=len(extracted),
        response=chat_result.response,
        app_name=chat_result.app_name,
        event_count=chat_result.event_count,
        learning_pack=pack,
    )
