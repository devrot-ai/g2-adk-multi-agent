"""ADK multi-agent app with summarization, classification, and grounded Q&A."""

from __future__ import annotations

import os
import re
from typing import Dict, List

from google.adk.agents import Agent


# Use a configurable model so quota/model switches do not require code edits.
# Default uses a model verified to work with the current prototype API key.
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")


def extractive_hint(text: str, max_sentences: int = 3) -> Dict[str, object]:
    """Return lightweight extraction hints used by the summarizer.

    This tool gives deterministic structure (length stats + key sentences)
    that the model can use before writing the final summary.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return {
            "status": "error",
            "error_message": "Input text is empty.",
        }

    sentences: List[str] = [s.strip() for s in re.split(r"(?<=[.!?])\\s+", cleaned) if s.strip()]
    sentence_count = len(sentences)

    if sentence_count == 0:
        return {
            "status": "success",
            "word_count": len(cleaned.split()),
            "character_count": len(cleaned),
            "key_points": [cleaned[:280]],
        }

    clipped_max = max(1, min(max_sentences, 5))
    key_points = sentences[:clipped_max]

    return {
        "status": "success",
        "word_count": len(cleaned.split()),
        "character_count": len(cleaned),
        "sentence_count": sentence_count,
        "key_points": key_points,
    }


def classify_text(text: str) -> Dict[str, object]:
    """Return a simple deterministic topic + sentiment hint for input text."""
    cleaned = " ".join(text.lower().split())
    if not cleaned:
        return {
            "status": "error",
            "error_message": "Input text is empty.",
        }

    topic_keywords = {
        "cloud": ["cloud", "serverless", "kubernetes", "deployment", "run", "gcp"],
        "ai": ["ai", "agent", "model", "gemini", "llm", "inference"],
        "finance": ["revenue", "profit", "market", "stock", "cost", "budget"],
        "education": ["student", "course", "teacher", "school", "learning", "exam"],
    }
    topic_scores = {
        topic: sum(1 for kw in keywords if kw in cleaned)
        for topic, keywords in topic_keywords.items()
    }
    top_topic = max(topic_scores, key=topic_scores.get)
    predicted_topic = top_topic if topic_scores[top_topic] > 0 else "general"

    positive = ["good", "great", "excellent", "improve", "success", "fast", "easy"]
    negative = ["bad", "poor", "slow", "issue", "risk", "error", "difficult"]
    pos_score = sum(1 for w in positive if w in cleaned)
    neg_score = sum(1 for w in negative if w in cleaned)
    sentiment = "neutral"
    if pos_score > neg_score:
        sentiment = "positive"
    elif neg_score > pos_score:
        sentiment = "negative"

    return {
        "status": "success",
        "predicted_topic": predicted_topic,
        "topic_scores": topic_scores,
        "sentiment": sentiment,
        "sentiment_scores": {
            "positive": pos_score,
            "negative": neg_score,
        },
    }


def context_answer_support(context: str, question: str, max_sentences: int = 3) -> Dict[str, object]:
    """Extract likely supporting sentences from context for grounded Q&A."""
    cleaned_context = " ".join(context.split())
    cleaned_question = " ".join(question.lower().split())

    if not cleaned_context:
        return {
            "status": "error",
            "error_message": "Context is empty.",
        }
    if not cleaned_question:
        return {
            "status": "error",
            "error_message": "Question is empty.",
        }

    question_terms = {
        t for t in re.findall(r"[a-zA-Z0-9]+", cleaned_question) if len(t) > 2
    }
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_context) if s.strip()]
    scored: List[tuple[int, str]] = []
    for sentence in sentences:
        sentence_terms = {
            t for t in re.findall(r"[a-zA-Z0-9]+", sentence.lower()) if len(t) > 2
        }
        overlap = len(question_terms.intersection(sentence_terms))
        scored.append((overlap, sentence))

    clipped_max = max(1, min(max_sentences, 5))
    top_sentences = [s for score, s in sorted(scored, key=lambda x: x[0], reverse=True) if score > 0][:clipped_max]
    if not top_sentences and sentences:
        top_sentences = sentences[:1]

    return {
        "status": "success",
        "question_terms": sorted(question_terms),
        "supporting_sentences": top_sentences,
    }


summarizer_sub_agent = Agent(
    name="summarizer_specialist",
    model=MODEL_ID,
    description="Creates concise summaries from long text.",
    instruction=(
        "You are a summarization specialist. Always call extractive_hint first. "
        "Then produce: (1) 2-4 concise bullets and (2) one sentence labeled 'Core takeaway'."
    ),
    tools=[extractive_hint],
)


classifier_sub_agent = Agent(
    name="classifier_specialist",
    model=MODEL_ID,
    description="Classifies text by topic and sentiment.",
    instruction=(
        "You are a classification specialist. Always call classify_text first. "
        "Return topic, sentiment, and a brief justification."
    ),
    tools=[classify_text],
)


qa_sub_agent = Agent(
    name="qa_specialist",
    model=MODEL_ID,
    description="Answers questions grounded only in supplied context.",
    instruction=(
        "You are a grounded Q&A specialist. Always call context_answer_support first. "
        "Answer only from the provided context. If context is insufficient, explicitly say so."
    ),
    tools=[context_answer_support],
)


root_agent = Agent(
    name="assistant_coordinator",
    model=MODEL_ID,
    description="Routes requests to specialized sub-agents for summarization, classification, and Q&A.",
    instruction=(
        "You are a coordinator with three specialists: summarizer, classifier, and grounded Q&A. "
        "Delegate to the best sub-agent based on user intent. "
        "If intent is ambiguous, ask one clarifying question. "
        "Keep answers concise and actionable."
    ),
    sub_agents=[summarizer_sub_agent, classifier_sub_agent, qa_sub_agent],
)
