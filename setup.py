#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="unimacro",
    version="0.0.1",
    description="Unimacro",
    author="Jiang Yiheng",
    author_email="jiangyiheng@corp.netease.com",
    python_requires=">=3.6",
    packages=["unimacro"],
    entry_points={
        "console_scripts": [
            "unimacro = unimacro.unimacro:main",
        ]
    },
)
