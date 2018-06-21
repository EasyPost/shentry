import collections
import threading
import subprocess
import os
import json
import mock
import pwd
import socket

import pytest

try:
    from BaseHTTPServer import HTTPServer
    from BaseHTTPServer import BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer
    from http.server import BaseHTTPRequestHandler


Request = collections.namedtuple('Request', ['command', 'path', 'headers', 'body'])


class SentryHTTPServer(HTTPServer):
    timeout = 0.1

    def __init__(self, *args, **kwargs):
        requests = kwargs.pop('requests')
        HTTPServer.__init__(self, *args, **kwargs)
        self.requests = requests

    def handle_timeout(self):
        pass


class SentryHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body_len = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(body_len)
        request = Request(command=self.command, path=self.path, headers=dict(self.headers.items()), body=body)
        self.server.requests.append(request)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        body = json.dumps({'status': 'ok'}).encode('utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class UUTHTTPServer(object):
    def __init__(self):
        self.running = False
        self.address = None
        self._thread = None
        self.requests = []
        self._started = threading.Condition()

    @property
    def uri(self):
        return 'http://sentry:password@{0}/'.format(':'.join(map(str, self.address)))

    def run(self):
        self.running = True
        httpd = SentryHTTPServer(('127.0.0.1', 0), SentryHTTPRequestHandler, requests=self.requests)
        self.address = httpd.server_address
        self._started.acquire()
        self._started.notify_all()
        self._started.release()
        while self.running:
            httpd.handle_request()

    def start(self):
        t = threading.Thread(target=self.run)
        self._thread = t
        t.start()
        self._started.acquire()
        self._started.wait()
        self._started.release()

    def stop(self):
        if self.running:
            self.running = False
            self._thread.join()


@pytest.yield_fixture
def http_server():
    t_s = UUTHTTPServer()
    t_s.start()
    yield t_s
    t_s.stop()


FAIL_NO_OUTPUT = '''#!/bin/bash

exit 1
'''

FAIL_LONG_OUTPUT = '''#!/bin/bash

head -c 2000 /usr/share/dict/words
tail -c 2000 /usr/share/dict/words >&2

exit 1
'''


@pytest.fixture
def scripts(tmpdir):
    paths = {}
    for script in ('FAIL_NO_OUTPUT', 'FAIL_LONG_OUTPUT'):
        with open(os.path.join(str(tmpdir), script), 'w') as f:
            f.write(globals()[script])
            os.fchmod(f.fileno(), 0o700)
        paths[script] = os.path.join(str(tmpdir), script)
    return paths


def test_no_output(http_server, scripts):
    subprocess.check_call(
        ['shentry.py', scripts['FAIL_NO_OUTPUT']],
        env={
            'SHELL_SENTRY_DSN': http_server.uri,
            'TZ': 'UTC',
        }
    )
    # ensure that the http server has processed all requests
    http_server.stop()
    assert len(http_server.requests) == 1
    req = http_server.requests[0]
    assert req.command == 'POST'
    body = json.loads(req.body.decode('utf-8'))
    assert body == {
        'device': mock.ANY,
        'event_id': mock.ANY,
        'extra': {
            'PATH': mock.ANY,
            'TZ': 'UTC',
            '_sent_with': mock.ANY,
            'command': scripts['FAIL_NO_OUTPUT'],
            'duration': mock.ANY,
            'load_average_at_exit': mock.ANY,
            'returncode': 1,
            'shell': '/bin/sh',
            'start_time': mock.ANY,
            'username': pwd.getpwuid(os.getuid()).pw_name,
            'working_directory': mock.ANY,
        },
        'fingerprint': mock.ANY,
        'message': 'Command `{0}` failed with code 1.\n'.format(scripts['FAIL_NO_OUTPUT']),
        'platform': 'other',
        'server_name': socket.gethostname(),
        'level': 'error',
        'sdk': {
            'name': 'shentry',
            'version': mock.ANY,
        },
        'timestamp': mock.ANY,
    }


def test_multi_kb_output(http_server, scripts):
    subprocess.check_call(
        ['shentry.py', scripts['FAIL_LONG_OUTPUT']],
        env={
            'SHELL_SENTRY_DSN': http_server.uri,
            'TZ': 'UTC',
        }
    )
    # ensure that the http server has processed all requests
    http_server.stop()
    assert len(http_server.requests) == 1
    req = http_server.requests[0]
    assert req.command == 'POST'
    body = json.loads(req.body.decode('utf-8'))
    assert body == {
        'device': mock.ANY,
        'event_id': mock.ANY,
        'extra': {
            'PATH': mock.ANY,
            'TZ': 'UTC',
            '_sent_with': mock.ANY,
            'command': scripts['FAIL_LONG_OUTPUT'],
            'duration': mock.ANY,
            'load_average_at_exit': mock.ANY,
            'returncode': 1,
            'shell': '/bin/sh',
            'start_time': mock.ANY,
            'username': pwd.getpwuid(os.getuid()).pw_name,
            'working_directory': mock.ANY,
        },
        'fingerprint': mock.ANY,
        'message': mock.ANY,
        'platform': 'other',
        'server_name': socket.gethostname(),
        'level': 'error',
        'sdk': {
            'name': 'shentry',
            'version': mock.ANY,
        },
        'timestamp': mock.ANY,
    }
    assert body['message'].startswith(
        'Command `{0}` failed with code 1.\n\nExcerpt of stderr:\n'.format(scripts['FAIL_LONG_OUTPUT'])
    )
