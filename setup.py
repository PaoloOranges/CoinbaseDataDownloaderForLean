#!/usr/bin/env python3
"""
Setup configuration for Coinbase Data Downloader package
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [line.strip() for line in requirements_file.read_text().split('\n')
                   if line.strip() and not line.startswith('#')]

setup(
    name="coinbase-downloader",
    version="1.0.0",
    description="Download historical quote data from Coinbase REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Development Team",
    packages=find_packages(exclude=['tests*', '.agents', '.github', '.vscode']),
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'coinbase-downloader=coinbase_downloader.cli.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
