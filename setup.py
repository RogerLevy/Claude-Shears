#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="shears",
    version="0.1.0",
    description="Interactive console tool for managing Claude Code projects and conversations",
    author="Claude",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "textual>=0.41.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "shears = shears.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)