from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchHit:
    authors: list[str]
    key: str
    title: str
    venue: str = ""
    year: str = ""
    raw_bibtex: str | None = None
    renamed_bibtex: str | None = None


@dataclass
class BibtexResult:
    query: str
    matched: bool
    selected_hit: SearchHit | None = None
    candidates: list[SearchHit] = field(default_factory=list)
    error: str | None = None

    @property
    def bibtex(self) -> str:
        if not self.selected_hit or not self.selected_hit.renamed_bibtex:
            return ""
        return self.selected_hit.renamed_bibtex


@dataclass
class BatchBibtexResult:
    items: list[BibtexResult]

    @property
    def matched_count(self) -> int:
        return sum(1 for item in self.items if item.matched)

    @property
    def missed_count(self) -> int:
        return len(self.items) - self.matched_count

    @property
    def combined_bibtex(self) -> str:
        return "\n\n".join(item.bibtex for item in self.items if item.bibtex)
