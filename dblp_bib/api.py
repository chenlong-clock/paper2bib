from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .client import DBLPBibClient
from .cli import serialize_batch_result, serialize_result
from .models import SearchHit

app = FastAPI(title="DBLP Bib API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = DBLPBibClient()


class SingleBibtexRequest(BaseModel):
    title: str = Field(min_length=1)
    limit: int = 10
    preference: str = "venueFirst"
    rename_style: str = "authorYearTitle"
    custom_pattern: str = "{author}{year}{title}"


class BatchBibtexRequest(BaseModel):
    titles: list[str] = Field(min_length=1)
    limit: int = 10
    preference: str = "venueFirst"
    rename_style: str = "authorYearTitle"
    custom_pattern: str = "{author}{year}{title}"


class SelectedHitRequest(BaseModel):
    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    venue: str = ""
    year: str = ""
    rename_style: str = "authorYearTitle"
    custom_pattern: str = "{author}{year}{title}"


class SearchCandidatesRequest(BaseModel):
    title: str = Field(min_length=1)
    limit: int = 10
    preference: str = "dblp"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/bibtex")
def create_bibtex(payload: SingleBibtexRequest) -> dict:
    result = client.search_bibtex(
        payload.title,
        limit=payload.limit,
        preference=payload.preference,
        rename_style=payload.rename_style,
        custom_pattern=payload.custom_pattern,
    )
    return serialize_result(result)


@app.post("/search")
def search_candidates(payload: SearchCandidatesRequest) -> dict:
    hits = client.search_candidates(
        payload.title,
        limit=payload.limit,
        preference=payload.preference,
        use_metadata_hint=False,
    )
    return {
        "query": payload.title,
        "candidates": [
            {
                "title": hit.title,
                "authors": hit.authors,
                "venue": hit.venue,
                "year": hit.year,
                "key": hit.key,
            }
            for hit in hits
        ],
    }


@app.post("/bibtex/batch")
def create_batch_bibtex(payload: BatchBibtexRequest) -> dict:
    result = client.batch_search_bibtex(
        payload.titles,
        limit=payload.limit,
        preference=payload.preference,
        rename_style=payload.rename_style,
        custom_pattern=payload.custom_pattern,
    )
    return serialize_batch_result(result)


@app.post("/bibtex/by-key")
def create_bibtex_from_hit(payload: SelectedHitRequest) -> dict:
    result = client.bibtex_from_hit(
        SearchHit(
            authors=payload.authors,
            key=payload.key,
            title=payload.title,
            venue=payload.venue,
            year=payload.year,
        ),
        rename_style=payload.rename_style,
        custom_pattern=payload.custom_pattern,
    )
    return serialize_result(result)
