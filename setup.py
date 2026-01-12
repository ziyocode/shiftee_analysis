#!/usr/bin/env python
"""Setup script for shiftee-analysis package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="shiftee-analysis",
    version="0.1.0",
    description="Shiftee 근무 데이터 분석 및 초과근로 적정성 판정 도구",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shiftee Analysis Team",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.4",
        "pydantic-settings>=2.2",
        "playwright>=1.40",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "openpyxl>=3.1.0",
        "python-dateutil>=2.8.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "shiftee-analyze=shiftee.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
)
