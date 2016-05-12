**Shentry** is a single-file Python script which will run the wrapped command and, if it fails, post an event to
Sentry. By default, if the wrapped script succeeds (exists with code 0), stdout/stderr are squashed, similarly to
[shuck](https://github.com/thwarted/shuck) or [chronic](https://joeyh.name/code/moreutils/).

It reads its configuration from the environment variable `$SHELL_SENTRY_DSN` and, if such a variable is found,
removes it from the environment before calling the wrapped program. If the environment variable is not present or 
is empty
