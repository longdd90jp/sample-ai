# tools.py
import asyncio
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Concurrency limiter to avoid tool call storms under load
_TOOL_SEMAPHORE = asyncio.Semaphore(10)  # tune per environment

class WebResult(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    content: str = Field(..., description="Extracted text content (truncated)")

class FetchError(RuntimeError):
    """Raised when web fetch fails after retries."""

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.8, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError)),
)
async def http_get(url: str, timeout_s: int = 10) -> str:
    """
    Robust HTTP GET with retries for transient failures.
    Raises httpx.HTTPStatusError on 4xx/5xx after response.raise_for_status().
    """
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_s),
        follow_redirects=True,
        headers={"User-Agent": "agentic-ai-bot/1.0"},
    ) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

def extract_title_and_text(html: str) -> tuple[Optional[str], str]:
    """
    Parse HTML safely and extract title + visible text.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    # Remove scripts/styles that pollute text extraction
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return title, text

async def web_fetch(url: str, timeout_s: int = 10, max_chars: int = 8000) -> WebResult:
    """
    Fetch and parse a web page with concurrency limits, retries, and safe parsing.
    """
    async with _TOOL_SEMAPHORE:
        try:
            raw_html = await http_get(url, timeout_s=timeout_s)
            title, text = extract_title_and_text(raw_html)

            # Truncate to control token cost
            snippet = text[:max_chars]

            return WebResult(url=url, title=title, content=snippet)
        except Exception as e:
            raise FetchError(f"Failed to fetch {url}: {e}") from e