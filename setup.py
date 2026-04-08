#!/usr/bin/env python

from setuptools import setup

setup(
    name="shentry",
    version="2.0.0",
    author="EasyPost",
    author_email="oss@easypost.com",
    url="https://github.com/easypost/shentry",
    license="ISC",
    packages=[],
    scripts=["shentry.py"],
    keywords=["logging"],
    description="Wrap a program in sentry!",
    python_requires=">=3.9, <4",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
    ],
)
