0.4.0
-----
- pass through SIGTERM, SIGQUIT, and SIGINT to the child process
- do not send empty tags to Sentry
- (internal) switch tests from circleci to travisci

0.3.2
-----
- Move `level`, `server_name` and `sdk` from `tags` to top-level
- Add Python 3.6 to tox tests

0.3.1
-----
- Fix bug with loading large command outputs
- Add more tests

0.3.0
-----
- Add support for using `requests` if it's importable
- Add support for outbound proxies via `$SHELL_SENTRY_PROXY` or `/etc/shentry_proxy`
