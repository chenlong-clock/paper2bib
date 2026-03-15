from __future__ import annotations

import html
import json
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import BatchBibtexResult, BibtexResult, SearchHit
from .naming import rename_bibtex_entry

SEARCH_API = "https://dblp.org/search/publ/api"
RECORD_API = "https://dblp.org/rec/{key}.bib"
OPENALEX_API = "https://api.openalex.org/works"
USER_AGENT = "dblp-bib/0.1.0 (+https://github.com/)"


class DBLPBibClient:
    def __init__(
        self,
        *,
        timeout: float = 20.0,
        hint_timeout: float = 3.0,
        cache_ttl: float = 600.0,
    ) -> None:
        self.timeout = timeout
        self.hint_timeout = hint_timeout
        self.cache_ttl = cache_ttl
        self._search_cache: dict[tuple[str, int], tuple[float, list[SearchHit]]] = {}
        self._bibtex_cache: dict[str, tuple[float, str]] = {}

    def search_bibtex(
        self,
        title: str,
        *,
        limit: int = 10,
        preference: str = "venueFirst",
        rename_style: str = "authorYearTitle",
        custom_pattern: str = "{author}{year}{title}",
        used_keys: set[str] | None = None,
    ) -> BibtexResult:
        query = title.strip()
        if not query:
            raise ValueError("title must not be empty")

        key_pool = used_keys if used_keys is not None else set()
        try:
            candidates = self.search_hits(query, limit=limit)
            if should_retry_with_hint(query, candidates):
                candidates = self.expand_hits_with_metadata_hint(query, candidates, limit=limit)
            sorted_candidates = sort_hits(candidates, preference, query=query)
            selected = sorted_candidates[0] if sorted_candidates else None

            if not selected:
                return BibtexResult(query=query, matched=False, candidates=[])

            raw_bibtex = self.fetch_bibtex(selected.key)
            resolved = SearchHit(
                authors=selected.authors,
                key=selected.key,
                title=selected.title,
                venue=selected.venue,
                year=selected.year,
                raw_bibtex=raw_bibtex,
            )
            resolved.renamed_bibtex = rename_bibtex_entry(
                raw_bibtex,
                resolved,
                rename_style=rename_style,
                used_keys=key_pool,
                custom_pattern=custom_pattern,
            )
            return BibtexResult(
                query=query,
                matched=True,
                selected_hit=resolved,
                candidates=sorted_candidates,
            )
        except Exception as exc:
            return BibtexResult(query=query, matched=False, error=str(exc), candidates=[])

    def search_candidates(
        self,
        title: str,
        *,
        limit: int = 10,
        preference: str = "dblp",
        use_metadata_hint: bool = False,
    ) -> list[SearchHit]:
        query = title.strip()
        if not query:
            return []

        candidates = self.search_hits(query, limit=limit)
        if use_metadata_hint and should_retry_with_hint(query, candidates):
            candidates = self.expand_hits_with_metadata_hint(query, candidates, limit=limit)
        return sort_hits(candidates, preference, query=query)

    def batch_search_bibtex(
        self,
        titles: list[str],
        *,
        limit: int = 10,
        preference: str = "venueFirst",
        rename_style: str = "authorYearTitle",
        custom_pattern: str = "{author}{year}{title}",
    ) -> BatchBibtexResult:
        used_keys: set[str] = set()
        items = [
            self.search_bibtex(
                title,
                limit=limit,
                preference=preference,
                rename_style=rename_style,
                custom_pattern=custom_pattern,
                used_keys=used_keys,
            )
            for title in titles
            if title.strip()
        ]
        return BatchBibtexResult(items=items)

    def bibtex_from_hit(
        self,
        hit: SearchHit,
        *,
        rename_style: str = "authorYearTitle",
        custom_pattern: str = "{author}{year}{title}",
        used_keys: set[str] | None = None,
    ) -> BibtexResult:
        key_pool = used_keys if used_keys is not None else set()
        try:
            raw_bibtex = self.fetch_bibtex(hit.key)
            resolved = SearchHit(
                authors=hit.authors,
                key=hit.key,
                title=hit.title,
                venue=hit.venue,
                year=hit.year,
                raw_bibtex=raw_bibtex,
            )
            resolved.renamed_bibtex = rename_bibtex_entry(
                raw_bibtex,
                resolved,
                rename_style=rename_style,
                used_keys=key_pool,
                custom_pattern=custom_pattern,
            )
            return BibtexResult(
                query=hit.title,
                matched=True,
                selected_hit=resolved,
                candidates=[hit],
            )
        except Exception as exc:
            return BibtexResult(query=hit.title, matched=False, error=str(exc), candidates=[hit])

    def expand_hits_with_metadata_hint(
        self,
        query: str,
        existing_hits: list[SearchHit],
        *,
        limit: int,
    ) -> list[SearchHit]:
        hint = self.fetch_openalex_hint(query)
        if not hint:
            return existing_hits

        augmented_queries = []
        if hint.get("author"):
            augmented_queries.append(f"{query} {hint['author']}")
        if hint.get("year"):
            augmented_queries.append(f"{query} {hint['year']}")
        if hint.get("author") and hint.get("year"):
            augmented_queries.append(f"{query} {hint['author']} {hint['year']}")

        merged = {hit.key: hit for hit in existing_hits}
        for augmented_query in augmented_queries:
            for hit in self.search_hits(augmented_query, limit=limit):
                merged.setdefault(hit.key, hit)

        return list(merged.values())

    def search_hits(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        cache_key = (query, limit)
        cached_hits = self._search_cache_get(cache_key)
        if cached_hits is not None:
            return [clone_hit(hit) for hit in cached_hits]

        params = urlencode({"q": query, "h": str(limit), "format": "json"})
        payload = self._get_json(f"{SEARCH_API}?{params}")
        raw_hits = payload.get("result", {}).get("hits", {}).get("hit")
        if not raw_hits:
            return []

        hit_list = raw_hits if isinstance(raw_hits, list) else [raw_hits]
        items: list[SearchHit] = []
        for hit in hit_list:
            info = hit.get("info", {})
            author_field = info.get("authors", {}).get("author")
            authors = _normalize_authors(author_field)
            candidate = SearchHit(
                authors=authors,
                key=info.get("key", ""),
                title=strip_html(info.get("title", "")),
                venue=info.get("venue", ""),
                year=info.get("year", ""),
            )
            if candidate.key and candidate.title:
                items.append(candidate)
        self._search_cache_set(cache_key, items)
        return items

    def fetch_bibtex(self, key: str) -> str:
        cached_bibtex = self._bibtex_cache_get(key)
        if cached_bibtex is not None:
            return cached_bibtex

        request = Request(
            RECORD_API.format(key=key),
            headers={
                "Accept": "application/x-bibtex, text/plain;q=0.9, */*;q=0.8",
                "User-Agent": USER_AGENT,
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            bibtex = response.read().decode("utf-8")
            self._bibtex_cache_set(key, bibtex)
            return bibtex

    def _get_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_openalex_hint(self, query: str) -> dict[str, str] | None:
        try:
            params = urlencode({"search": query, "per-page": "5"})
            request = Request(
                f"{OPENALEX_API}?{params}",
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            )
            with urlopen(request, timeout=self.hint_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        results = payload.get("results", [])
        normalized_query = normalize_for_match(query)
        for item in results:
            title = item.get("display_name", "")
            if normalize_for_match(title) != normalized_query:
                continue

            authorships = item.get("authorships") or []
            first_author = ""
            if authorships:
                display_name = authorships[0].get("author", {}).get("display_name", "").strip()
                first_author = display_name.split()[-1] if display_name else ""

            year = item.get("publication_year")
            return {
                "author": first_author,
                "year": str(year) if year else "",
            }

        return None

    def _search_cache_get(self, key: tuple[str, int]) -> list[SearchHit] | None:
        payload = self._search_cache.get(key)
        if not payload:
            return None
        timestamp, hits = payload
        if time.time() - timestamp > self.cache_ttl:
            self._search_cache.pop(key, None)
            return None
        return hits

    def _search_cache_set(self, key: tuple[str, int], hits: list[SearchHit]) -> None:
        self._search_cache[key] = (time.time(), [clone_hit(hit) for hit in hits])

    def _bibtex_cache_get(self, key: str) -> str | None:
        payload = self._bibtex_cache.get(key)
        if not payload:
            return None
        timestamp, bibtex = payload
        if time.time() - timestamp > self.cache_ttl:
            self._bibtex_cache.pop(key, None)
            return None
        return bibtex

    def _bibtex_cache_set(self, key: str, bibtex: str) -> None:
        self._bibtex_cache[key] = (time.time(), bibtex)


def search_bibtex(title: str, **kwargs: object) -> BibtexResult:
    return DBLPBibClient().search_bibtex(title, **kwargs)


def batch_search_bibtex(titles: list[str], **kwargs: object) -> BatchBibtexResult:
    return DBLPBibClient().batch_search_bibtex(titles, **kwargs)


def sort_hits(hits: list[SearchHit], mode: str, *, query: str | None = None) -> list[SearchHit]:
    if mode == "dblp":
        return list(hits)
    return sorted(hits, key=lambda hit: hit_sort_key(hit, mode, query=query))


def hit_sort_key(hit: SearchHit, mode: str, *, query: str | None = None) -> tuple[int, int, int, str]:
    year_score = parse_year(hit.year)
    title_score = title_match_score(query, hit.title) if query else 0
    if mode == "yearDesc":
        return (-title_score, -year_score, -type_priority(hit, "venueFirst"), hit.title)
    return (-title_score, -type_priority(hit, mode), -year_score, hit.title)


def type_priority(hit: SearchHit, mode: str) -> int:
    hit_type = classify_hit(hit)
    priorities = (
        {"arxiv": 3, "venue": 2, "other": 1}
        if mode == "arxivFirst"
        else {"venue": 3, "other": 2, "arxiv": 1}
    )
    return priorities.get(hit_type, 0)


def classify_hit(hit: SearchHit) -> str:
    text = f"{hit.venue} {hit.key} {hit.title}".lower()
    if "arxiv" in text or "corr" in text or "abs/" in text:
        return "arxiv"
    if hit.venue.strip():
        return "venue"
    return "other"


def parse_year(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def strip_html(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())
def title_match_score(query: str, title: str) -> int:
    left = normalize_for_match(query)
    right = normalize_for_match(title)
    if not left or not right:
        return 0
    if left == right:
        return 6
    if right.startswith(f"{left} "):
        return 4
    if left in right:
        extra_words = max(0, len(right.split()) - len(left.split()))
        return max(1, 3 - min(extra_words, 2))
    if right in left:
        return 2

    left_words = set(left.split())
    right_words = set(right.split())
    overlap = len(left_words & right_words)
    if overlap >= max(2, min(len(left_words), len(right_words)) - 1):
        return 2
    if overlap:
        return 1
    return 0


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_html(value).lower()).strip()


def should_retry_with_hint(query: str, hits: list[SearchHit]) -> bool:
    normalized_query = normalize_for_match(query)
    if not normalized_query or not hits:
        return False

    return not any(normalize_for_match(hit.title) == normalized_query for hit in hits)


def _normalize_authors(value: object) -> list[str]:
    if isinstance(value, list):
        return [author.get("text", "") if isinstance(author, dict) else str(author) for author in value if author]
    if isinstance(value, dict):
        text = value.get("text", "")
        return [text] if text else []
    if value:
        return [str(value)]
    return []


def clone_hit(hit: SearchHit) -> SearchHit:
    return SearchHit(
        authors=[*hit.authors],
        key=hit.key,
        title=hit.title,
        venue=hit.venue,
        year=hit.year,
        raw_bibtex=hit.raw_bibtex,
        renamed_bibtex=hit.renamed_bibtex,
    )
