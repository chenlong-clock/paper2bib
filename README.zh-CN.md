<h1 align="center">🫧 DBLP BibTeX Renamer</h1>

<p align="center">
  <a href="./pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" /></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.9-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="./docs/index.html"><img alt="Web" src="https://img.shields.io/badge/web-self--hosted-orange?style=flat-square&logo=googlechrome&logoColor=white" /></a>
</p>

把论文标题直接变成干净、可用、可批量处理的 BibTeX。

## 快速信息

- 🪪 License：[MIT](./LICENSE)
- 🏷️ 版本：`0.1.0`
- 🌐 Webpages：[中文页面](./docs/index.html) | [English page](./docs/en.html)
- 🛠️ 部署方式：前端静态页和 FastAPI 后端均需自行部署

🌏 语言：
- [English README](./README.md)
- 中文（本文件）

🌐 网页：
- [中文页面](./docs/index.html)
- [English page](./docs/en.html)

## 项目定位

这是一个同时支持 `网页`、`CLI`、`Python 库` 和 `HTTP API` 的小工具，适合：
- 想快速从 DBLP 拉 BibTeX 的学生和研究者
- 想批量整理参考文献的论文作者
- 想把 BibTeX 能力接进自己工作流、插件或服务的人

## 目录结构

```text
docs/         前端静态页面（自行部署）
dblp_bib/     Python 包、CLI、FastAPI
pyproject.toml
setup.py
```

## 安装

```bash
pip install paper2bib
```

开发模式：

```bash
python3 -m pip install -e .
```

## 网页模式

先启动 API：

```bash
uvicorn dblp_bib.api:app --reload
```

再在仓库根目录启动静态服务：

```bash
python3 -m http.server 8000
```

访问：

```text
http://localhost:8000/docs/
```

## CLI 模式

```bash
paper2bib "Attention Is All You Need"
```

批量模式：

```bash
paper2bib --file titles.txt --preference venueFirst --output refs.bib
```

## Python 库模式

```python
from dblp_bib import search_bibtex, batch_search_bibtex

single = search_bibtex("Attention Is All You Need", preference="venueFirst")
batch = batch_search_bibtex([
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
], preference="venueFirst")
```

## API 模式

```bash
uvicorn dblp_bib.api:app --reload
curl http://127.0.0.1:8000/health
```

## BibTeX key 命名规则

默认命名规则：

```text
作者姓氏 + 年份 + 标题前三个有效词
```

例如：

```text
vaswani2017attentionAllNeed
```

## 发布到 PyPI

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```
