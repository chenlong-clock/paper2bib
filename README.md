# 🫧 DBLP BibTeX Renamer

[![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)](./pyproject.toml)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)

Turn paper titles into clean, reusable BibTeX entries.

## Quick Info

- 🪪 License: [MIT](./LICENSE)
- 🏷️ Version: `0.1.0`
- 🌐 Webpages: [中文页面](./docs/index.html) | [English page](./docs/en.html)

🌏 Language:
- English (this file)
- [简体中文 README](./README.zh-CN.md)

🌐 Web:
- [中文页面](./docs/index.html)
- [English page](./docs/en.html)

## What It Is

This project provides one core capability in four forms:
- Web UI
- CLI
- Python package
- FastAPI service

Use it when you want to search DBLP by paper title and quickly get renamed BibTeX keys for your workflow.

## Project Layout

```text
docs/         Web frontend (GitHub Pages friendly)
dblp_bib/     Python package, CLI, FastAPI
pyproject.toml
setup.py
```

## Install

```bash
pip install .
```

For development:

```bash
python3 -m pip install -e .
```

## Web Mode

Start API:

```bash
uvicorn dblp_bib.api:app --reload
```

Serve static files from repo root:

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/docs/
```

## CLI Mode

```bash
dblp-bib "Attention Is All You Need"
```

Batch mode:

```bash
dblp-bib --file titles.txt --preference venueFirst --output refs.bib
```

## Python Mode

```python
from dblp_bib import search_bibtex, batch_search_bibtex

single = search_bibtex("Attention Is All You Need", preference="venueFirst")
batch = batch_search_bibtex([
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
], preference="venueFirst")
```

## API Mode

```bash
uvicorn dblp_bib.api:app --reload
curl http://127.0.0.1:8000/health
```

## BibTeX Key Naming

Default key style:

```text
<author-last-name><year><first-keywords-of-title>
```

Example:

```text
vaswani2017attentionAllNeed
```

## Publish to PyPI

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```
