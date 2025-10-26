#!/usr/bin/env python3
"""
Setup script for FlashLogger package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="FlashLogger",
    version="1.0.0",
    author="Dieter J Kybelksties",
    author_email="github@kybelksties.com",
    description="Advanced console logging with color support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kingkybel/FlashLogger",
    packages=find_packages(),
    package_data={
        'flashlogger': ['config/*.json'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.8",
    install_requires=[
        "colorama>=0.4.0",
        "Pygments>=2.0.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "mypy"],
    },
    keywords="logging console color ansi configuration",
    project_urls={
        "Bug Reports": "https://github.com/kingkybel/FlashLogger/issues",
        "Source": "https://github.com/kingkybel/FlashLogger",
    },
)
