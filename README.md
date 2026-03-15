<h1 align="center">🫧 PaperBib</h1>

<p align="center">
  <a href="./pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" /></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.9-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="./docs/index.html"><img alt="Web" src="https://img.shields.io/badge/web-self--hosted-orange?style=flat-square&logo=googlechrome&logoColor=white" /></a>
</p>

<p align="center"><b>Type a paper title. Get clean BibTeX. Keep your references organized.</b></p>

## Quick Info

- Project name: `PaperBib`
- Package name (PyPI): `paper2bib`
- CLI command: `paper2bib`
- License: [MIT](./LICENSE)
- Language: English (this file) | [简体中文 README](./README.zh-CN.md)

## Why It Is Useful

- Search DBLP directly from paper titles
- Generate BibTeX ready to copy or export
- Batch mode for large reading lists
- Consistent key naming across your references
- Same engine for Web, CLI, Python, and API

## Quick Start

Install from PyPI:

```bash
pip install paper2bib
```

Run one query:

```bash
paper2bib "Attention Is All You Need"
```

Run batch mode:

```bash
paper2bib --file titles.txt --preference venueFirst --output refs.bib
```

## Web Mode (Self-Hosted)

Start backend API:

```bash
uvicorn dblp_bib.api:app --reload
```

Serve static frontend from repository root:

```bash
python3 -m http.server 8000
```

Open in browser:

```text
http://localhost:8000/docs/
```

## Python Library

```python
from dblp_bib import search_bibtex, batch_search_bibtex

single = search_bibtex("Attention Is All You Need", preference="venueFirst")
batch = batch_search_bibtex([
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
], preference="venueFirst")
```

## HTTP API

```bash
uvicorn dblp_bib.api:app --reload
curl http://127.0.0.1:8000/health
```

## Project Layout

```text
docs/         Web frontend (self-hosted static files)
dblp_bib/     Python package, CLI, FastAPI
pyproject.toml
setup.py
```

## Acknowledgement

- [DBLP](https://dblp.org) for the paper metadata and bibliographic ecosystem.
- Contributors building open-source research tooling and citation workflows.
