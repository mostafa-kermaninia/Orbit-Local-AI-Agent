from __future__ import annotations

import urllib.parse
import webbrowser


def open_youtube(query: str) -> dict[str, object]:
    """Open the first YouTube search result when yt-dlp can resolve it.

    Falls back to the YouTube results page if extraction fails.
    """
    query = " ".join(query.split())
    if not query:
        return {"ok": False, "error": "Empty YouTube query."}

    try:
        from yt_dlp import YoutubeDL

        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        entries = info.get("entries") or []
        if entries:
            first = entries[0]
            video_id = first.get("id")
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open_new_tab(url)
                return {"ok": True, "query": query, "title": first.get("title", ""), "url": url}
    except Exception:
        pass

    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    webbrowser.open_new_tab(url)
    return {"ok": True, "query": query, "url": url, "fallback": "search_results"}
