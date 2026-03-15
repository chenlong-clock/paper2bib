<h1 align="center">🫧 Paper2Bib</h1>

<p align="center">
  <a href="./pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue?style=flat-square" /></a>
  <a href="https://www.python.org"><img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.9-3776AB?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="./docs/index.html"><img alt="Web" src="https://img.shields.io/badge/web-self--hosted-orange?style=flat-square&logo=googlechrome&logoColor=white" /></a>
</p>

<p align="center"><b>输入论文标题，快速拿到干净 BibTeX，让参考文献整理更顺手。</b></p>

## 快速信息

- 项目名：`Paper2Bib`
- 包名（PyPI）：`paper2bib`（小写）
- 命令名：`paper2bib`
- 许可证：[MIT](./LICENSE)
- 语言：[English README](./README.md) | 中文（本文件）

## 为什么好用

- 直接用论文标题搜索 DBLP
- 生成可复制、可导出的 BibTeX
- 支持批量模式，适合长文献清单
- 支持统一命名规则，便于个人库管理
- Web / CLI / Python / API 共用同一套核心逻辑

## 快速开始

从 PyPI 安装：

```bash
pip install paper2bib
```

单篇查询：

```bash
paper2bib "Attention Is All You Need"
```

批量模式：

```bash
paper2bib --file titles.txt --preference venueFirst --output refs.bib
```

## 网页模式（自部署）

启动后端 API：

```bash
uvicorn dblp_bib.api:app --reload
```

在仓库根目录启动前端静态服务：

```bash
python3 -m http.server 8000
```

浏览器访问：

```text
http://localhost:8000/docs/
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

## HTTP API

```bash
uvicorn dblp_bib.api:app --reload
curl http://127.0.0.1:8000/health
```

## 项目结构

```text
docs/         前端静态页面（自行部署）
dblp_bib/     Python 包、CLI、FastAPI
pyproject.toml
setup.py
```

## Acknowledgement

- 感谢 [DBLP](https://dblp.org) 提供论文元数据与书目信息生态。
- 感谢所有持续建设开源科研工具链的贡献者。
