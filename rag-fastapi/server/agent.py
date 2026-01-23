# agent.py
from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from guardrails import validate_answer
from rag import retrieve, rerank_bm25  # updated reranker name
from tools import web_fetch, FetchError


MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")  # cost-aware default

openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY must be set")

llm = ChatOpenAI(model=MODEL, temperature=0, openai_api_key=openai_api_key)

SYSTEM_PROMPT = """You are a production-grade agent.
You may use tools when truly necessary.
Return ONLY valid JSON (no markdown) with keys:
- answer: string
- sources: array of strings
- cost_tokens: integer
Do not reveal internal reasoning or scratchpads."""

# ---------- Helpers: JSON-only enforcement ----------
def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # remove leading/trailing ```json fences if present
        t = t.strip("`")
        # If the model returned "json\n{...}", remove first line label
        lines = t.splitlines()
        if lines and lines[0].strip().lower() in {"json", "javascript"}:
            t = "\n".join(lines[1:])
    return t.strip()

def _best_effort_json(text: str) -> Optional[dict]:
    t = _strip_fences(text)
    try:
        return json.loads(t)
    except Exception:
        return None


# ---------- Tool calling schema ----------
# We avoid "fake URL" and instead ask the model for a structured tool call.
TOOL_DECISION_PROMPT = """Decide if you must use a web fetch tool.
If you need a fetch, output JSON ONLY:
{"action":"web_fetch","url":"https://...","reason":"..."}
If no tool needed, output JSON ONLY:
{"action":"final","reason":"..."}"""

FINAL_PROMPT_TEMPLATE = """You are answering the user's query.
Use the enterprise context (if any) and any fetched web content (if any).
Return ONLY valid JSON:
{"answer": "...", "sources": ["..."], "cost_tokens": 0}
Keep the answer factual and concise.
"""


# ---------- RAG caching: retrieve once per run ----------
def _build_enterprise_context(index, query: str, *, k: int = 6, top_n: int = 3, max_chars: int = 3500) -> Tuple[str, List[str]]:
    """
    Retrieve once and rerank; return a bounded context string + sources.
    """
    hits = retrieve(index, query, k=k)
    top_docs = rerank_bm25(query, hits, top_n=top_n)

    chunks: List[str] = []
    sources: List[str] = []
    total = 0

    for d in top_docs:
        src = d.metadata.get("source", "enterprise")
        sources.append(str(src))
        snippet = d.page_content.strip()
        if not snippet:
            continue
        snippet = snippet[:1200]  # cap per chunk
        if total + len(snippet) > max_chars:
            break
        chunks.append(f"[SOURCE:{src}] {snippet}")
        total += len(snippet)

    return "\n\n".join(chunks), sources


async def _llm_ainvoke(messages: List[Any]) -> AIMessage:
    """
    Stable async invocation across modern LangChain builds.
    """
    return await llm.ainvoke(messages)


async def agent_run(query: str, index, *, step_budget: int = 2, tool_timeout_s: int = 12) -> Dict[str, Any]:
    """
    Production-oriented agent loop:
    - Retrieves enterprise context once (cached)
    - Optionally performs limited tool calls (structured)
    - Never leaks scratchpad into user-visible messages
    - Forces JSON-only output and validates schema/policy
    """

    # Cache enterprise context once per run (not every loop iteration)
    enterprise_context, enterprise_sources = _build_enterprise_context(index, query)

    # Private scratchpad for internal state only (never appended as HumanMessage)
    _scratchpad: List[str] = []
    sources: List[str] = list(dict.fromkeys(enterprise_sources))  # dedupe while preserving order

    # Base messages visible to the model (no internal chain-of-thought)
    base_messages: List[Any] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]

    # Only attach enterprise context once (bounded)
    if enterprise_context:
        base_messages.append(
            SystemMessage(content=f"Enterprise context (use if relevant):\n{enterprise_context}")
        )

    # Limited tool loop (structured decisions)
    for step in range(step_budget):
        decision_msg = [
            *base_messages,
            SystemMessage(content=TOOL_DECISION_PROMPT),
        ]

        decision = await _llm_ainvoke(decision_msg)
        payload = _best_effort_json(decision.content)

        if not payload or payload.get("action") not in {"web_fetch", "final"}:
            # Fail closed on malformed tool directive: proceed without tools
            _scratchpad.append(f"Tool decision malformed at step={step}; skipping tools.")
            break

        if payload["action"] == "final":
            _scratchpad.append(f"Model chose final at step={step}: {payload.get('reason','')}")
            break

        # Tool execution
        url = payload.get("url", "")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            _scratchpad.append(f"Invalid URL in tool call: {url!r}; skipping.")
            break

        try:
            result = await asyncio.wait_for(web_fetch(url), timeout=tool_timeout_s)
            sources.append(str(result.url))
            _scratchpad.append(f"Fetched: {result.url} title={result.title!r}")

            # Add fetched content as SYSTEM message (not Human), to avoid “agent thought in user channel”
            base_messages.append(
                SystemMessage(
                    content=f"Fetched web page:\nURL: {result.url}\nTitle: {result.title}\nContent:\n{result.content}"
                )
            )
        except (asyncio.TimeoutError, FetchError) as e:
            _scratchpad.append(f"Tool failed: {e}; continuing without web context.")
            break

    # Final response: JSON-only
    final_messages = [
        *base_messages,
        SystemMessage(content=FINAL_PROMPT_TEMPLATE),
    ]
    final = await _llm_ainvoke(final_messages)

    parsed = _best_effort_json(final.content)

    # If JSON invalid, fail closed with safe fallback (no raw model dump)
    if not parsed:
        parsed = {
            "answer": "I couldn't produce a valid structured response. Please retry.",
            "sources": sources,
            "cost_tokens": 0,
        }

    # Always include sources we actually used/collected
    parsed["sources"] = list(dict.fromkeys((parsed.get("sources") or []) + sources))

    # Token metering: placeholder here (best practice is OpenTelemetry + provider token usage)
    # We keep cost_tokens present and non-negative for schema validation.
    parsed["cost_tokens"] = int(parsed.get("cost_tokens") or 0)

    # Validate schema + policy (pydantic<2 version of guardrails)
    obj = validate_answer(parsed)
    return obj.dict()