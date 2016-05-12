#!/usr/bin/env python

# NOTE: This code should work with Python 2.6, 2.7, 3.2, 3.3, 3.4, and 3.5

from __future__ import print_function

try:
    from urllib.parse import urlparse
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError, URLError


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

VERSION = '0.1'


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
        dsn = os.environ.get('SHELL_SENTRY_DSN', '')
        if not dsn:
            return None
        else:
            del os.environ['SHELL_SENTRY_DSN']
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
            'server_name': socket.gethostname(),
            'logger': logger,
            'fingerprint': fingerprint,
            'platform': 'other',
            'device': {
                'name': uname[0],
                'version': uname[2],
                'build': uname[3]
            },
            'extra': {}
        }
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
        req = Request(self.uri, data=data, headers=headers)
        try:
            with closing(urlopen(req, timeout=self.TIMEOUT)) as f:
                f.read()
            return True
        except HTTPError as e:
            print('Error {0} sending to Sentry'.format(e.code), file=sys.stderr)
            print(e.read(), file=sys.stderr)
            return False
        except URLError as e:
            print('Error {0} sending to Sentry'.format(e.reason), file=sys.stderr)
            return False


def main():
    extra_context = {
        'PATH': os.environ.get('PATH', ''),
        'username': pwd.getpwuid(os.getuid()).pw_name
    }
    if 'TZ' in os.environ:
        extra_context['TZ'] = os.environ['TZ']
    client = SimpleSentryClient.new_from_environment()
    # get the command
    command = sys.argv[1:]
    i_am_shell = False
    if command[0] == '-c':
        i_am_shell = True
        command = command[1:]
    if command[0] == '--':
        command = command[1:]
    shell = os.environ.get('SHELL', '/bin/sh')
    if i_am_shell or 'shentry' in shell:
        shell = '/bin/sh'
    extra_context['shell'] = shell
    command_ws = ' '.join(command)
    full_command = [shell, '-c', command_ws]
    # if we couldn't configure sentry, just pass through
    if client is None:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.execv(shell, full_command)
        print('Unable to execv({0}, {1})'.format(shell, repr(full_command)), file=sys.stderr)
        return 1
    try:
        working_dir = tempfile.mkdtemp()
        with open(os.path.join(working_dir, 'stdout'), 'w+') as stdout:
            with open(os.path.join(working_dir, 'stderr'), 'w+') as stderr:
                start_time = time.time()
                p = subprocess.Popen(full_command, stdout=stdout, stderr=stderr, shell=False,
                                     preexec_fn=lambda: signal.signal(signal.SIGPIPE, signal.SIG_DFL))
                end_time = time.time()
                extra_context['start_time'] = start_time
                extra_context['duration'] = end_time - start_time
                extra_context['command'] = command_ws
                extra_context['load_average_at_exit'] = ' '.join(map(str, os.getloadavg()))
                if p.wait() != 0:
                    stderr.seek(0, 0)
                    stderr_head = stderr.read(400)
                    message = 'Command `{0}` failed.\n'.format(command_ws)
                    if stderr_head:
                        message += '\nHead of stderr:\n' + stderr_head
                    stdout.seek(0, 0)
                    stdout_head = stdout.read(400)
                    if stdout_head:
                        message += '\nHead of stdout:\n' + stdout_head
                    client.send_event(
                        message=message,
                        level='error',
                        fingerprint=[socket.gethostname(), command_ws],
                        extra_context=extra_context,
                    )
    finally:
        shutil.rmtree(working_dir)


if __name__ == '__main__':
    sys.exit(main())
