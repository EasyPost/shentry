#!/usr/bin/env python

# Copyright (c) 2016, EasyPost <oss@easypost.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby
# granted, provided that the above copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
# AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.


# NOTE: This code should work with Python 2.6, 2.7, 3.2, 3.3, 3.4, 3.5, and 3.6

from __future__ import print_function

try:
    from urllib.parse import urlparse
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError, URLError

try:
    import requests
    has_requests = True
except ImportError:
    has_requests = False


import datetime
import json
import os
import pwd
import sys
import time
import uuid
import subprocess
import tempfile
import shutil
import signal
import socket

from contextlib import closing

VERSION = '0.3.2'


def read_systemwide_config():
    try:
        with open('/etc/shentry_dsn', 'r') as f:
            return f.read().strip()
    except Exception:
        return None


def _get_proxy_url():
    if 'SHELL_SENTRY_PROXY' in os.environ:
        return os.environ['SHELL_SENTRY_PROXY']
    try:
        with open('/etc/shentry_proxy', 'r') as f:
            return f.read().strip()
    except Exception:
        pass
    return None


def _send_urllib2(uri, headers, data, timeout):
    req = Request(uri, data=data, headers=headers)
    try:
        with closing(urlopen(req, timeout=timeout)) as f:
            f.read()
        return True
    except HTTPError as e:
        print('Error {0} sending to Sentry'.format(e.code), file=sys.stderr)
        print(e.read(), file=sys.stderr)
        return False
    except URLError as e:
        print('Error {0} sending to Sentry'.format(e.reason), file=sys.stderr)
        return False


def _send_requests(uri, headers, data, timeout):
    try:
        kwargs = {}
        proxy_url = _get_proxy_url()
        if proxy_url is not None:
            kwargs['proxies'] = {
                'http': proxy_url,
                'https': proxy_url
            }
        resp = requests.post(
            uri, headers=headers, data=data, timeout=timeout,
            **kwargs
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print('Error {0!r} sending to Sentry'.format(e), file=sys.stderr)
        return False


if has_requests:
    send_to_sentry = _send_requests
else:
    send_to_sentry = _send_urllib2


class SimpleSentryClient(object):
    TIMEOUT = 5
    SENTRY_VERSION = 5
    USER_AGENT = 'shentry/{0}'.format(VERSION)

    def __init__(self, dsn, uri, public, secret, project_id):
        self.dsn = dsn
        self.uri = uri
        self.public = public
        self.secret = secret
        self.project_id = project_id

    @classmethod
    def new_from_environment(cls):
        dsn = os.environ.pop('SHELL_SENTRY_DSN', '')
        if not dsn:
            dsn = read_systemwide_config()
        if not dsn:
            return None
        else:
            try:
                dsn_fields = urlparse(dsn)
                keys, netloc = dsn_fields.netloc.split('@', 1)
                if ':' in keys:
                    public, private = keys.split(':', 1)
                else:
                    public = keys
                    private = ''
                project_id = dsn_fields.path.lstrip('/')
                uri = '{proto}://{netloc}/api/{project_id}/store/'.format(
                    proto=dsn_fields.scheme, netloc=netloc,
                    project_id=project_id,
                )
                return cls(dsn, uri, public, private, project_id)
            except Exception as e:
                print('Error parsing sentry DSN {0}: {1}'.format(dsn, e), file=sys.stderr)

    def send_event(self, message, level, fingerprint, logger='', culprit=None, extra_context={}):
        event_id = uuid.uuid4().hex
        now = int(time.time())
        uname = os.uname()
        event = {
            'event_id': event_id,
            'timestamp': datetime.datetime.utcnow().isoformat().split('.', 1)[0],
            'message': message,
            'level': level,
            'server_name': socket.gethostname(),
            'tags': [],
            'sdk': {
                'name': 'shentry',
                'version': VERSION,
            },
            'fingerprint': fingerprint,
            'platform': 'other',
            'device': {
                'name': uname[0],
                'version': uname[2],
                'build': uname[3]
            },
            'extra': {}
        }
        if logger:
            event['logger'] = logger
        if culprit is not None:
            event['culprit'] = culprit
        event['extra'].update(extra_context)
        headers = {
            'X-Sentry-Auth': (
                'Sentry sentry_version={self.SENTRY_VERSION}, '
                'sentry_client={self.USER_AGENT}, '
                'sentry_timestamp={now}, '
                'sentry_key={self.public}, '
                'sentry_secret={self.secret}'
            ).format(now=now, self=self),
            'User-Agent': self.USER_AGENT,
            'Content-Type': 'application/json',
        }
        if os.environ.get('SHELL_SENTRY_VERBOSE', '0') == '1':
            print('Sending to shentry', file=sys.stderr)
            print(event, file=sys.stderr)
        data = json.dumps(event).encode('utf-8')
        return send_to_sentry(uri=self.uri, headers=headers, data=data, timeout=self.TIMEOUT)


def get_command(argv):
    # get the command
    i_am_shell = False
    command = argv
    if command[0] == '-c':
        i_am_shell = True
        command = command[1:]
    if command[0] == '--':
        command = command[1:]
    shell = os.environ.get('SHELL', '/bin/sh')
    if i_am_shell or 'shentry' in shell:
        shell = '/bin/sh'
    command_ws = ' '.join(command)
    full_command = [shell, '-c', command_ws]
    return full_command, command_ws, shell


def show_usage():
    print('Usage: shentry [-c] command [...]', file=sys.stderr)
    print('', file=sys.stderr)
    print('Runs COMMAND, sending the output to Sentry if it exits non-0', file=sys.stderr)
    print('Takes sentry DSN from $SHELL_SENTRY_DSN or /etc/shentry_dsn', file=sys.stderr)


def read_snippet(fo, max_length):
    fo.seek(0, os.SEEK_END)
    length = fo.tell()
    rv = []
    fo.seek(0, os.SEEK_SET)
    read_all = False
    if length > max_length:
        top = int(max_length / 2) - 8
        bottom = max_length - top
        top = fo.read(top).decode('utf-8', 'ignore')
        rv.append(top)
        if not top.endswith('\n'):
            rv.append('\n')
        rv.append('\n[snip]\n')
        fo.seek(-1 * bottom, os.SEEK_END)
        rv.append(fo.read(bottom).decode('utf-8', 'ignore'))
    else:
        rv.append(fo.read().decode('utf-8', 'ignore'))
        read_all = True
    return ''.join(rv), read_all


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        show_usage()
        return 2
    extra_context = {
        'PATH': os.environ.get('PATH', ''),
        'username': pwd.getpwuid(os.getuid()).pw_name
    }
    if 'TZ' in os.environ:
        extra_context['TZ'] = os.environ['TZ']
    client = SimpleSentryClient.new_from_environment()
    full_command, command_ws, shell = get_command(argv[1:])
    extra_context['command'] = command_ws
    extra_context['shell'] = shell
    # if we couldn't configure sentry, just pass through
    if client is None:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.execv(shell, full_command)
        print('Unable to execv({0}, {1})'.format(shell, repr(full_command)), file=sys.stderr)
        return 1
    working_dir = None
    try:
        working_dir = tempfile.mkdtemp()
        with open(os.path.join(working_dir, 'stdout'), 'w+b') as stdout:
            with open(os.path.join(working_dir, 'stderr'), 'w+b') as stderr:
                start_time = time.time()
                p = subprocess.Popen(full_command, stdout=stdout, stderr=stderr, shell=False,
                                     preexec_fn=lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL))
                extra_context['start_time'] = start_time
                extra_context['load_average_at_exit'] = ' '.join(map(str, os.getloadavg()))
                extra_context['working_directory'] = os.getcwd()
                extra_context['_sent_with'] = send_to_sentry.__name__
                if p.wait() != 0:
                    end_time = time.time()
                    extra_context['duration'] = end_time - start_time
                    code = p.returncode
                    extra_context['returncode'] = code
                    stderr_head, stderr_is_all = read_snippet(stderr, 700)
                    message = 'Command `{0}` failed with code {1}.\n'.format(command_ws, code)
                    if stderr_head:
                        if stderr_is_all:
                            message += '\nstderr:\n'
                        else:
                            message += '\nExcerpt of stderr:\n'
                        message += stderr_head
                    stdout_head, stdout_is_all = read_snippet(stdout, 200 + (700 - len(stderr_head)))
                    if stdout_head:
                        if stdout_is_all:
                            message += '\nstdout:\n'
                        else:
                            message += '\nExcerpt of stdout:\n'
                        message += stdout_head
                    client.send_event(
                        message=message,
                        level='error',
                        fingerprint=[socket.gethostname(), command_ws],
                        extra_context=extra_context,
                    )
    finally:
        if working_dir is not None:
            shutil.rmtree(working_dir)


if __name__ == '__main__':
    sys.exit(main())
