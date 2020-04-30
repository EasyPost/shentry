#!/usr/bin/env python

from setuptools import setup


setup(
    name="shentry",
    version="0.4.0",
    author="EasyPost",
    author_email="oss@easypost.com",
    url="https://github.com/easypost/shentry",
    license="ISC",
    packages=[],
    scripts=['shentry.py'],
    keywords=["logging"],
    description="Wrap a program in sentry!",
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
    ]
)
