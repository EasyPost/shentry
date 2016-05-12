#!/usr/bin/env python

from setuptools import setup


setup(
    name="shentry",
    version="0.1",
    author="EasyPost",
    author_email="oss@easypost.com",
    url="https://github.com/easypost/shentry",
    license="ISC",
    packages=[],
    scripts=['shentry.py'],
    keywords=["logging"],
    description="Wrap a program in sentry!",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
    ]
)
