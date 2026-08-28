from __future__ import annotations

import html
import re
import ssl
import time
import urllib.parse
import urllib.request
import webbrowser
from typing import Any

import httpx
from bs4 import BeautifulSoup


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
)
_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "close",
}


def web_search(query: str) -> dict[str, object]:
    query = " ".join(query.split())
    if not query:
        return {"ok": False, "error": "Empty search query."}
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    opened = webbrowser.open_new_tab(url)
    return {"ok": bool(opened), "query": query, "url": url}


def open_url(url: str) -> dict[str, object]:
    url = url.strip()
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"ok": False, "error": "Only normal http/https URLs are allowed."}
    opened = webbrowser.open_new_tab(url)
    return {"ok": bool(opened), "url": url}


def _validate_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only normal http/https URLs are allowed.")
    return url


def _get_text_httpx(url: str, timeout_seconds: float) -> tuple[str, str, str]:
    transport = httpx.HTTPTransport(retries=2)
    with httpx.Client(
        transport=transport,
        follow_redirects=True,
        timeout=httpx.Timeout(float(timeout_seconds), connect=float(timeout_seconds)),
        headers=_HEADERS,
        http2=False,
        trust_env=True,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text, str(response.url), response.headers.get("content-type", "")


def _get_text_urllib(url: str, timeout_seconds: float) -> tuple[str, str, str]:
    # urllib gives us a second TLS/network stack path on Windows. This is useful
    # when a VPN/proxy/ISP terminates an httpx/OpenSSL connection unexpectedly.
    request = urllib.request.Request(url, headers=_HEADERS, method="GET")
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=float(timeout_seconds), context=context) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        text = raw.decode(charset, errors="replace")
        return text, response.geturl(), response.headers.get("Content-Type", "")


def _fetch_text(url: str, timeout_seconds: float) -> tuple[str, str, str]:
    errors: list[str] = []

    for attempt in range(2):
        try:
            return _get_text_httpx(url, timeout_seconds)
        except Exception as exc:
            errors.append(f"httpx[{attempt + 1}]: {exc}")
            time.sleep(0.35 * (attempt + 1))

    try:
        return _get_text_urllib(url, timeout_seconds)
    except Exception as exc:
        errors.append(f"urllib: {exc}")

    raise RuntimeError(" | ".join(errors))


def _extract_readable_text(raw_html: str, char_limit: int) -> tuple[str, str]:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "canvas", "template", "nav", "footer"]):
        tag.decompose()
    title = " ".join((soup.title.get_text(" ", strip=True) if soup.title else "").split())

    root = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[str] = []
    for node in root.find_all(["h1", "h2", "h3", "p", "li", "blockquote"]):
        text = " ".join(node.get_text(" ", strip=True).split())
        if len(text) >= 35:
            blocks.append(text)
    if not blocks:
        blocks = [" ".join(root.get_text(" ", strip=True).split())]
    text = "\n".join(blocks)
    return title, text[: max(1000, int(char_limit))]


def read_webpage(url: str, timeout_seconds: float = 12.0, char_limit: int = 7000) -> dict[str, Any]:
    """Fetch visible text from a public HTML page for the local LLM to summarize."""
    try:
        url = _validate_url(url)
        raw_html, final_url, content_type = _fetch_text(url, timeout_seconds)
        ctype = (content_type or "").lower()
        if "html" not in ctype and "text/" not in ctype and ctype:
            return {"ok": False, "error": f"Unsupported content type: {ctype}", "url": final_url}
        title, text = _extract_readable_text(raw_html, char_limit)
        if not text.strip():
            return {"ok": False, "error": "No readable text was found on the page.", "url": final_url}
        return {
            "ok": True,
            "url": final_url,
            "title": title,
            "content": text,
            "note": "Summarize only this fetched page content; do not claim you read anything not included here.",
        }
    except Exception as exc:
        return {"ok": False, "error": f"Could not read webpage: {exc}", "url": url}


def _duckduckgo_results(query: str, timeout_seconds: float, max_results: int) -> list[dict[str, str]]:
    # GET is intentionally used instead of POST; it survives more VPN/proxy setups.
    endpoint = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    raw_html, _, _ = _fetch_text(endpoint, timeout_seconds)
    soup = BeautifulSoup(raw_html, "html.parser")
    results: list[dict[str, str]] = []
    for result in soup.select(".result"):
        anchor = result.select_one("a.result__a")
        if not anchor:
            continue
        href = anchor.get("href", "")
        if href.startswith("//duckduckgo.com/l/?") or "duckduckgo.com/l/?" in href:
            parsed = urllib.parse.urlparse("https:" + href if href.startswith("//") else href)
            href = urllib.parse.parse_qs(parsed.query).get("uddg", [href])[0]
        title = " ".join(anchor.get_text(" ", strip=True).split())
        snippet_node = result.select_one(".result__snippet")
        snippet = " ".join(snippet_node.get_text(" ", strip=True).split()) if snippet_node else ""
        if href.startswith("http"):
            results.append({"title": html.unescape(title), "url": href, "snippet": html.unescape(snippet)})
        if len(results) >= max_results:
            break
    return results


def _bing_results(query: str, timeout_seconds: float, max_results: int) -> list[dict[str, str]]:
    endpoint = "https://www.bing.com/search?q=" + urllib.parse.quote_plus(query)
    raw_html, _, _ = _fetch_text(endpoint, timeout_seconds)
    soup = BeautifulSoup(raw_html, "html.parser")
    results: list[dict[str, str]] = []
    for item in soup.select("li.b_algo"):
        anchor = item.select_one("h2 a")
        if not anchor:
            continue
        href = (anchor.get("href") or "").strip()
        if not href.startswith("http"):
            continue
        title = " ".join(anchor.get_text(" ", strip=True).split())
        snippet_node = item.select_one(".b_caption p")
        snippet = " ".join(snippet_node.get_text(" ", strip=True).split()) if snippet_node else ""
        results.append({"title": html.unescape(title), "url": href, "snippet": html.unescape(snippet)})
        if len(results) >= max_results:
            break
    return results


def _search_candidates(query: str, timeout_seconds: float, max_results: int) -> tuple[list[dict[str, str]], str, list[str]]:
    errors: list[str] = []
    # Bing first so the visible browser search and parsed result list normally match.
    # DuckDuckGo remains a fallback when Bing is unavailable on the current network.
    providers = [
        ("Bing", _bing_results),
        ("DuckDuckGo", _duckduckgo_results),
    ]
    for provider_name, provider in providers:
        try:
            results = provider(query, timeout_seconds, max_results)
            if results:
                return results, provider_name, errors
            errors.append(f"{provider_name}: no parseable results")
        except Exception as exc:
            errors.append(f"{provider_name}: {exc}")
    return [], "", errors


def _visible_search_url(provider: str, query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    if provider == "DuckDuckGo":
        return "https://duckduckgo.com/?q=" + encoded
    return "https://www.bing.com/search?q=" + encoded


def research_web(
    query: str,
    timeout_seconds: float = 12.0,
    max_results: int = 5,
    char_limit: int = 7000,
    visual: bool = True,
    search_page_wait_seconds: float = 1.8,
    source_page_wait_seconds: float = 1.6,
) -> dict[str, Any]:
    """Visibly research the web, read top result pages, and return their text.

    The user's normal browser is used as a presentation layer: the search-results
    page is opened first and then each selected source is opened in a real browser
    tab. Page text is fetched separately in the background because scraping text
    from the rendered browser UI with mouse/keyboard automation is fragile.
    """
    query = " ".join(query.split()).strip()
    if not query:
        return {"ok": False, "error": "Empty research query."}

    candidates, provider, search_errors = _search_candidates(
        query,
        float(timeout_seconds),
        max(1, int(max_results)),
    )
    if not candidates:
        return {
            "ok": False,
            "error": "All web search providers failed. " + " | ".join(search_errors),
            "query": query,
        }

    # Make the research process visible on the user's own desktop/browser.
    # We intentionally open URLs directly rather than clicking screen coordinates;
    # this survives browser zoom, themes, window sizes, and result-layout changes.
    opened_urls: list[str] = []
    if visual:
        try:
            search_url = _visible_search_url(provider, query)
            webbrowser.open_new_tab(search_url)
            opened_urls.append(search_url)
            time.sleep(max(0.0, float(search_page_wait_seconds)))
        except Exception:
            # Visible choreography must never make the actual research fail.
            pass

    sources: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if visual:
            try:
                webbrowser.open_new_tab(candidate["url"])
                opened_urls.append(candidate["url"])
                time.sleep(max(0.0, float(source_page_wait_seconds)))
            except Exception:
                pass

        page = read_webpage(candidate["url"], timeout_seconds=timeout_seconds, char_limit=char_limit)
        sources.append({
            "rank": index,
            "title": candidate["title"],
            "url": candidate["url"],
            "snippet": candidate["snippet"],
            "content": page.get("content", "") if page.get("ok") else "",
            "fetch_ok": bool(page.get("ok")),
            "fetch_error": page.get("error", "") if not page.get("ok") else "",
        })

    readable_count = sum(1 for source in sources if source["fetch_ok"] and source["content"])

    return {
        "ok": True,
        "query": query,
        "search_provider": provider,
        "visual_research": bool(visual),
        "opened_browser_tabs": len(opened_urls),
        "candidate_count": len(sources),
        "readable_source_count": readable_count,
        "sources": sources,
        "instruction": (
            "Synthesize the answer across ALL returned sources, not just the first source. "
            "Prefer points supported by multiple sources. Mention uncertainty or disagreement when present. "
            "Answer only from these search snippets and fetched source texts. "
            "If the evidence is insufficient, say so instead of filling gaps from memory."
        ),
    }
