<h1 align="center">🫧 Paper2Bib</h1>

<p align="center">
  <a href="./pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" /></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.9-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="./docs/index.html"><img alt="Web" src="https://img.shields.io/badge/web-self--hosted-orange?style=flat-square&logo=googlechrome&logoColor=white" /></a>
</p>

<p align="center"><b>Type a paper title. Get clean BibTeX. Keep your references organized.</b></p>

Paper2Bib (`paper2bib`) is a Python package and CLI that searches DBLP from paper titles and returns clean BibTeX entries.

Language: English (this file) | [简体中文 README](./README.zh-CN.md)

## What You Can Do

- Search DBLP directly from paper titles
- Generate BibTeX ready to copy or export
- Run batch conversion for large reading lists
- Keep consistent key naming across your references
- Use the same core engine from Web, CLI, Python, and HTTP API

## Installation

```bash
pip install paper2bib
```

## CLI Usage

Single title:

```bash
paper2bib "Attention Is All You Need"
```

Batch mode:

```bash
paper2bib --file titles.txt --preference venueFirst --output refs.bib
```

## Web UI

Open the static pages directly:

<p align="center">
  <a href="./docs/index.html"><img alt="Open Chinese Webpage" src="https://img.shields.io/badge/Open-Webpage%20%28ZH%29-2ea44f?style=for-the-badge&logo=googlechrome&logoColor=white" /></a>
  <a href="./docs/en.html"><img alt="Open English Webpage" src="https://img.shields.io/badge/Open-Webpage%20%28EN%29-0366d6?style=for-the-badge&logo=googlechrome&logoColor=white" /></a>
</p>

<p align="center">
  <img alt="Paper2Bib Web UI Chinese" src="./docs/assets/web-ch.png" width="47%" />
  <img alt="Paper2Bib Web UI English" src="./docs/assets/web-en.png" width="47%" />
</p>

Self-hosted local run:

1. Start backend API:

```bash
uvicorn dblp_bib.api:app --reload
```

2. Serve static frontend from repository root:

```bash
python3 -m http.server 8000
```

3. Open in browser:

```text
http://localhost:8000/docs/
```

## Python Usage

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
