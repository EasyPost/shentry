import os
import tempfile
import socket
import subprocess

import mock
import pytest

import shentry


class _Any(object):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ANY = _Any()


@pytest.mark.parametrize('argv,expected_full_command,expected_command_ws,expected_shell', (
    (['/foo/bar'], ['/bin/bash', '-c', '/foo/bar'], '/foo/bar', '/bin/bash'),
    (['/foo/bar', 'arg1', 'arg2'], ['/bin/bash', '-c', '/foo/bar arg1 arg2'], '/foo/bar arg1 arg2', '/bin/bash'),
    (['-c', 'ls | head'], ['/bin/sh', '-c', 'ls | head'], 'ls | head', '/bin/sh'),
))
def test_get_command(mocker, argv, expected_full_command, expected_command_ws, expected_shell):
    mocker.patch('os.environ', autospec=True)
    os.environ.get.return_value = '/bin/bash'
    assert shentry.get_command(argv) == (expected_full_command, expected_command_ws, expected_shell)
    os.environ.get.assert_called_once_with('SHELL', '/bin/sh')


class TestSimpleSentryClient(object):
    def test_new_from_environment(self, mocker):
        mocker.patch.dict('os.environ', {'SHELL_SENTRY_DSN': 'https://pub:priv@sentry.test/1'})
        client = shentry.SimpleSentryClient.new_from_environment()
        assert client.uri == 'https://sentry.test/api/1/store/'
        assert client.public == 'pub'
        assert client.secret == 'priv'
        assert client.project_id == '1'

    def test_new_from_environment_with_file(self, mocker):
        mocker.patch.dict('os.environ', {'SHELL_SENTRY_DSN': ''})
        mocker.patch.object(shentry, 'read_systemwide_config', return_value='https://pub:priv@sentry.test/2')
        client = shentry.SimpleSentryClient.new_from_environment()
        assert client.uri == 'https://sentry.test/api/2/store/'
        assert client.public == 'pub'
        assert client.secret == 'priv'
        assert client.project_id == '2'


def test_main(mocker, tmpdir):
    mock_client = mock.Mock(autospec=shentry.SimpleSentryClient)
    mocker.patch('shentry.SimpleSentryClient.new_from_environment', return_value=mock_client)
    mocker.patch('tempfile.mkdtemp', return_value=str(tmpdir))
    mocker.patch.dict('os.environ', {'SHELL': '/bin/fish', 'PATH': 'A_PATH', 'TZ': 'UTC'})
    mock_popen = mock.Mock(autospec=subprocess.Popen)
    mocker.patch('subprocess.Popen', return_value=mock_popen)
    mock_popen.wait.return_value = 1
    mock_popen.returncode = 1
    shentry.main(['shentry', '/bin/ls'])
    tempfile.mkdtemp.assert_called_once_with()
    mock_client.send_event.assert_called_once_with(
        message='Command `/bin/ls` failed with code 1.\n',
        level='error',
        fingerprint=[socket.gethostname(), '/bin/ls'],
        extra_context={
            'username': ANY,
            'shell': '/bin/fish',
            'load_average_at_exit': ANY,
            'start_time': ANY,
            'command': '/bin/ls',
            'duration': ANY,
            'PATH': 'A_PATH',
            'TZ': 'UTC',
            'returncode': 1,
            'working_directory': ANY,
            '_sent_with': ANY,
        }
    )
