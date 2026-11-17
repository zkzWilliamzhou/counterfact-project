"""Compatibility shim for setuptools < 61 (which ignores PEP 621 metadata).

Modern build isolation uses ``pyproject.toml``. This file exists so that
``pip install --no-build-isolation`` on older hosts still produces a correctly
named, importable distribution instead of ``UNKNOWN-0.0.0``. Metadata here is
kept identical to ``pyproject.toml`` on purpose; review round 12 checks it.
"""

from setuptools import find_packages, setup

setup(
    name="counterfact-cli",
    version="0.1.0",
    description=(
        "Find the smallest tested environment change that flips a passing "
        "command into a specific failure"
    ),
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(include=["counterfact*"]),
    entry_points={"console_scripts": ["counterfact = counterfact.cli:main"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Debuggers",
    ],
)
