# Shentry

[![Build Status](https://travis-ci.com/EasyPost/shentry.svg?branch=master)](https://travis-ci.com/EasyPost/shentry)
[![Coverage Status](https://coveralls.io/repos/github/EasyPost/shentry/badge.svg)](https://coveralls.io/github/EasyPost/shentry)
[![Version](https://img.shields.io/github/v/tag/EasyPost/shentry)](https://github.com/EasyPost/shentry/releases)

**Shentry** is a single-file Python script which will run the wrapped
command and, if it fails, post an event to Sentry. By default, if the
wrapped script succeeds (exists with code 0), stdout/stderr are squashed,
similarly to [shuck](https://github.com/thwarted/shuck) or
[chronic](https://joeyh.name/code/moreutils/). It also always exits with
status 0 if events are able to be sent to Sentry.

## Installation

Put the file [`shentry.py`](shentry.py) anywhere in your `$PATH` under the
name `shentry` and mark it as executable.

If the `requests` library is available, it will be used; otherwise, the standard
`urllib2` / `urllib.request` methods are used. If `requests` is used, then
either `$SHELL_SENTRY_PROXY` or the contents of `/etc/shentry_proxy` can be
used to configure an outbound proxy.

The `setup.py` in this directory only exists for this project's dev tooling. To get
Shentry working on your machine, simply copy `shentry.py` wherever you need it.

## Usage

You might want a crontab that looks something like the following:

```sh
SHELL_SENTRY_DSN=https://pub:priv@app.getsentry.com/id

15 * * * * /usr/local/bin/shentry /usr/local/bin/run-periodic-scripts
```

You can also make shentry your `$SHELL` and wrap all commands in it:

```sh
SHELL_SENTRY_DSN=https://pub:priv@app.getsentry.com/id
SHELL=/usr/local/bin/shentry

15 * * * * /usr/local/bin/run-periodic-scripts
7 1 * * * /usr/local/bin/run-daily-scripts
```

In this case, it will run the wrapped commands through `/bin/sh` (otherwise, it will honor `$SHELL`).

### Environment Variables

Shentry reads its configuration from the environment variable `$SHELL_SENTRY_DSN`
and, if such a variable is found, removes it from the environment before
calling the wrapped program. If that environment variable is not present, shentry will look
for `$SENTRY_DSN` (and similarly remove it from the environment).
If you need to use `SENTRY_DSN` inside your project code, make sure to set both.
You may also in that case want to put a top-level try/except around your whole
program to prevent uncaught exceptions from trigging both your in-process sentry sdk
and also your extra-process shentry, since you very likely only want one or the other.
If neither of the environment variables are present or both
are empty, shentry will try to read a DSN from `/etc/shentry_dsn`. If no DSN
can be found, the wrapped will have normal behavior (stdout/stderr will go
to their normal file descriptors, exit code will be passed through, etc).

## License

This software is licensed under the ISC License, the full text of which can be found at [LICENSE.txt](LICENSE.txt).
