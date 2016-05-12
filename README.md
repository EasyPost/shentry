**Shentry** is a single-file Python script which will run the wrapped command and, if it fails, post an event to
Sentry. By default, if the wrapped script succeeds (exists with code 0), stdout/stderr are squashed, similarly to
[shuck](https://github.com/thwarted/shuck) or [chronic](https://joeyh.name/code/moreutils/). It also always exits
with status 0 if events are able to be sent to Sentry.

It reads its configuration from the environment variable `$SHELL_SENTRY_DSN`
and, if such a variable is found, removes it from the environment before
calling the wrapped program. If the environment variable is not present or
is empty, shentry will try to read a DSN from `/etc/shentry_dsn`. If no DSN
can be found, the wrapped will have normal behavior (stdout/stderr will go
to their normal file descriptors, exit code will be passed through, etc).


## Installation

Put the file [`shentry.py`](shentry.py) anywhere in your `$PATH` under the
name `shentry` and mark it as executable.

The `setup.py` in this directory only exists for `tox` to work (and run unit
tests). Don't bother using it; just copy `shentry.py` wherever you want it.

## Usage

You might want a crontab that looks something like the following:

    SHELL_SENTRY_DSN=https://pub:priv@app.getsentry.com/id

    15 * * * * /usr/local/bin/shentry /usr/local/bin/run-periodic-scripts

You can also make shentry your `$SHELL` and wrap all commands in it:

    SHELL_SENTRY_DSN=https://pub:priv@app.getsentry.com/id
    SHELL=/usr/local/bin/shentry

    15 * * * * /usr/local/bin/run-periodic-scripts
    7 1 * * * /usr/local/bin/run-daily-scripts

In this case, it will run the wrapped commands through `/bin/sh` (otherwise, it will honor `$SHELL`).
