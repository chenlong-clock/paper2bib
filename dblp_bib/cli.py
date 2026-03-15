from __future__ import annotations

import argparse
import json
from pathlib import Path

from .client import DBLPBibClient
from .models import BatchBibtexResult, BibtexResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search DBLP and export renamed BibTeX.")
    parser.add_argument("titles", nargs="*", help="Paper title words, or multiple titles when --batch-args is set.")
    parser.add_argument("-f", "--file", help="Read titles from a text file, one title per line.")
    parser.add_argument("-l", "--limit", type=int, default=10, help="How many DBLP hits to inspect.")
    parser.add_argument(
        "-p",
        "--preference",
        choices=["dblp", "venueFirst", "arxivFirst", "yearDesc"],
        default="venueFirst",
        help="How to choose among DBLP candidates.",
    )
    parser.add_argument(
        "-r",
        "--rename-style",
        choices=["authorYearTitle", "dblpKey", "custom"],
        default="authorYearTitle",
        help="How to rename the BibTeX entry key.",
    )
    parser.add_argument(
        "--custom-pattern",
        default="{author}{year}{title}",
        help="Pattern used when --rename-style custom is selected.",
    )
    parser.add_argument("-o", "--output", help="Write BibTeX output to a file.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--batch-args",
        action="store_true",
        help="Treat each positional argument as a separate title (advanced).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    titles = collect_titles(args.titles, args.file, args.batch_args)
    if not titles:
        parser.error("provide at least one title or --file")

    client = DBLPBibClient()
    result = client.batch_search_bibtex(
        titles,
        limit=args.limit,
        preference=args.preference,
        rename_style=args.rename_style,
        custom_pattern=args.custom_pattern,
    )

    if args.output:
        Path(args.output).write_text(result.combined_bibtex + ("\n" if result.combined_bibtex else ""), encoding="utf-8")

    if args.json:
        print(json.dumps(serialize_batch_result(result), ensure_ascii=False, indent=2))
        return

    if result.combined_bibtex:
        print(result.combined_bibtex)

    if result.missed_count:
        print(
            f"\nMatched {result.matched_count}/{len(result.items)} titles. "
            "Use --json to inspect misses.",
        )


def collect_titles(cli_titles: list[str], file_path: str | None, batch_args: bool) -> list[str]:
    if batch_args:
        titles = [title.strip() for title in cli_titles if title.strip()]
    elif cli_titles:
        titles = [" ".join(cli_titles).strip()]
    else:
        titles = []
    if file_path:
        file_titles = Path(file_path).read_text(encoding="utf-8").splitlines()
        titles.extend(title.strip() for title in file_titles if title.strip())
    return titles


def serialize_batch_result(result: BatchBibtexResult) -> dict:
    return {
        "matched_count": result.matched_count,
        "missed_count": result.missed_count,
        "items": [serialize_result(item) for item in result.items],
        "combined_bibtex": result.combined_bibtex,
    }


def serialize_result(result: BibtexResult) -> dict:
    return {
        "query": result.query,
        "matched": result.matched,
        "error": result.error,
        "bibtex": result.bibtex,
        "selected_hit": (
            {
                "title": result.selected_hit.title,
                "authors": result.selected_hit.authors,
                "venue": result.selected_hit.venue,
                "year": result.selected_hit.year,
                "key": result.selected_hit.key,
            }
            if result.selected_hit
            else None
        ),
        "candidates": [
            {
                "title": hit.title,
                "authors": hit.authors,
                "venue": hit.venue,
                "year": hit.year,
                "key": hit.key,
            }
            for hit in result.candidates
        ],
    }
