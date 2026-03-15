from setuptools import setup


setup(
    name="dblp-bib",
    version="0.1.0",
    description="Search DBLP and export renamed BibTeX from the browser, CLI, or FastAPI.",
    packages=["dblp_bib"],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.115,<1.0",
        "uvicorn>=0.30,<1.0",
    ],
    entry_points={
        "console_scripts": [
            "dblp-bib=dblp_bib.cli:main",
        ]
    },
)
