from __future__ import annotations

import re
import unicodedata

from .models import SearchHit

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "using",
    "via",
    "with",
}


def rename_bibtex_entry(
    raw_bibtex: str,
    hit: SearchHit,
    rename_style: str,
    used_keys: set[str],
    custom_pattern: str = "{author}{year}{title}",
) -> str:
    match = re.search(r"^@([^{]+)\{([^,]+),", raw_bibtex, flags=re.MULTILINE)
    if not match:
        return raw_bibtex

    entry_type = match.group(1)
    new_key = ensure_unique_key(
        build_entry_key(hit, rename_style=rename_style, custom_pattern=custom_pattern),
        used_keys,
    )
    return re.sub(
        r"^@([^{]+)\{([^,]+),",
        f"@{entry_type}{{{new_key},",
        raw_bibtex,
        count=1,
        flags=re.MULTILINE,
    )


def build_entry_key(
    hit: SearchHit,
    *,
    rename_style: str,
    custom_pattern: str = "{author}{year}{title}",
) -> str:
    if rename_style == "dblpKey":
        return sanitize_key(hit.key.replace("/", "_").replace(":", "_"))

    if rename_style == "custom":
        custom_key = (
            custom_pattern
            .replace("{author}", get_author_token(hit.authors))
            .replace("{year}", sanitize_key(hit.year or "noyear"))
            .replace("{title}", get_title_token(hit.title))
            .replace("{venue}", sanitize_key(hit.venue or "novenue"))
        )
        return sanitize_key(custom_key)

    return sanitize_key(
        f"{get_author_token(hit.authors)}{hit.year or 'noyear'}"
        f"{to_pascal_case(' '.join(get_title_words(hit.title, 3)))}"
    )


def extract_entry_key(bibtex: str) -> str:
    match = re.search(r"^@([^{]+)\{([^,]+),", bibtex, flags=re.MULTILINE)
    return match.group(2) if match else "-"


def ensure_unique_key(key: str, used_keys: set[str]) -> str:
    base = key or "untitled"
    candidate = base
    suffix = 2

    while candidate in used_keys:
        candidate = f"{base}{suffix}"
        suffix += 1

    used_keys.add(candidate)
    return candidate


def get_author_token(authors: list[str]) -> str:
    first_author = authors[0] if authors else "unknown"
    parts = re.sub(r"[^\w\s-]", "", normalize_text(first_author)).strip().split()
    return sanitize_key(parts[-1] if parts else "unknown").lower()


def get_title_words(title: str, count: int) -> list[str]:
    words = re.sub(r"[^\w\s-]", " ", normalize_text(title)).lower().split()
    filtered = [word for word in words if word not in STOP_WORDS]
    picked = filtered[:count]
    return picked if picked else ["paper"]


def get_title_token(title: str) -> str:
    return to_pascal_case(" ".join(get_title_words(title, 4)))


def sanitize_key(value: str) -> str:
    return "".join(
        part
        for part in re.sub(r"[^a-zA-Z0-9_-]+", " ", normalize_text(value)).strip().split()
    )


def to_pascal_case(value: str) -> str:
    words = value.split()
    chunks: list[str] = []
    for index, word in enumerate(words):
        lower = word.lower()
        if index == 0:
            chunks.append(lower)
        else:
            chunks.append(lower[:1].upper() + lower[1:])
    return "".join(chunks)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))

