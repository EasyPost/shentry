# CHANGELOG

## v1.0.0 (2023-11-20)

- Drops support for Python earlier than 3.7
- Adds support for Python 3.10-3.12

## v0.4.0

- pass through SIGTERM, SIGQUIT, and SIGINT to the child process
- do not send empty tags to Sentry
- (internal) switch tests from circleci to travisci

## v0.3.2

- Move `level`, `server_name` and `sdk` from `tags` to top-level
- Add Python 3.6 to tox tests

## v0.3.1

- Fix bug with loading large command outputs
- Add more tests

## v0.3.0

- Add support for using `requests` if it's importable
- Add support for outbound proxies via `$SHELL_SENTRY_PROXY` or `/etc/shentry_proxy`
