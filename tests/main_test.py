import argparse
import sys
from unittest import mock

import pytest

from todome.main import add
from todome.main import create_markdown_file
from todome.main import main
from todome.main import mark
from todome.main import md_elements_to_unicode
from todome.main import move
from todome.main import parse_args
from todome.main import read_print_file
from todome.main import remove
from todome.main import virtualenv_check
from todome.main import write_lines


def test_args():
    sys.argv = ['todome', '-a', 'test']
    args = parse_args()
    assert args.add == 'test'


def test_args_return_type():
    sys.argv = ['todome']
    args = parse_args()
    assert isinstance(args, argparse.Namespace)


@pytest.fixture
def mock_venv_false(monkeypatch):
    monkeypatch.setattr(sys, 'prefix', '/usr')
    monkeypatch.setattr(sys, 'base_prefix', '/usr')


@pytest.fixture
def mock_venv_true(monkeypatch):
    monkeypatch.setattr(sys, 'prefix', '/todome/venv')
    monkeypatch.setattr(sys, 'base_prefix', '/usr')


def test_virtualenv_false(mock_venv_false):
    env = virtualenv_check()
    assert env is False


def test_virtualenv_true(mock_venv_true):
    env = virtualenv_check()
    assert env is True


@pytest.mark.parametrize(
    'entry, add_mark, expected', [
        # True = Add a mark
        # False = Remove a mark
        ('[ ]', True, '[x]'),
        ('[x]', False, '[ ]'),
        ('[x]', True, '[x]'),
        ('[ ]', False, '[ ]'),
    ],
)
def test_mark_pass(entry, add_mark, expected):
    assert mark(entry, add_mark) == expected


@pytest.mark.parametrize(
    'entry, add_mark, expected', [
        # True = Add a mark
        # False = Remove a mark
        ('[ ]', True, '[ ]'),
        ('[x]', True, '[ ]'),
        ('[ ]', True, '[]'),
        ('[x]', False, '[x]'),
        ('[ ]', False, '[x]'),
        ('[x]', False, '[]'),
    ],
)
def test_mark_fail(entry, add_mark, expected):
    assert mark(entry, add_mark) != expected


def test_create_markdown_file_write(tmpdir):
    file = tmpdir.join('TODO.md')
    create_markdown_file(tmpdir)
    assert file.read() == '### Todo\n### In Progress\n### Completed\n'


def test_create_markdown_file_exists(tmpdir):
    with pytest.raises(SystemExit):
        create_markdown_file(tmpdir)
        create_markdown_file(tmpdir)


@pytest.mark.parametrize(
    'lines, expected', [
        (
            ['test\n', 'test\n', 'test\n'],
            ['test\n', 'test\n', 'test\n'],
        ),
    ],
)
def test_write_lines(lines, expected, tmpdir):
    file = tmpdir.join('TODO.md')
    write_lines(tmpdir, lines)
    assert file.readlines() == expected


def test_write_lines_FileNotFound_SystemExit():
    with pytest.raises(SystemExit):
        write_lines('dir_should_not_exist', [''])


def test_add_FileNotFound_SystemExit(tmpdir):
    with pytest.raises(SystemExit):
        add(tmpdir, 'test')


def test_add_lines_missing_categories(tmpdir):
    with pytest.raises(SystemExit):
        with mock.patch('todome.main.open', mock.mock_open(read_data='')):
            add(tmpdir, ['test'])


@mock.patch(
    'todome.main.open',
    mock.mock_open(read_data='###Todo\n### In Progress\n### Completed'),
)
def test_add(tmpdir):
    lines = add(tmpdir, 'New line')
    assert lines == [
        '###Todo\n',
        '- [ ] New line\n',
        '### In Progress\n',
        '### Completed',
    ]


@mock.patch(
    'todome.main.open',
    mock.mock_open(read_data='- [] test1\n- [] test2'),
)
def test_remove(tmpdir):
    lines = remove(tmpdir, [0])
    assert lines == ['- [] test2']


@mock.patch('todome.main.open', mock.mock_open(read_data=''))
def test_remove_IndexError_SystemExit(tmpdir):
    with pytest.raises(SystemExit):
        remove(tmpdir, [0])


def test_remove_FileNotFound_SystemExit():
    with pytest.raises(SystemExit):
        remove('dir_should_not_exist', [''])


@pytest.mark.parametrize(
    'data, expected', [
        (
            '### Todo\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n' +
            '### In Progress\n' +
            '### Completed\n',
            [
                '### Todo\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n',
                '### In Progress\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n',
                '### Completed\n',
            ],
        ),
    ],
)
def test_move(data, expected, tmpdir):
    with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
        lines = move(tmpdir, [0], False)
        assert lines == expected


@pytest.mark.parametrize(
    'data, expected', [
        (
            '### Todo\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n' +
            '### In Progress\n' +
            '### Completed\n',
            [
                '### Todo\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n',
                '### In Progress\n',
                '### Completed\n',
                '- [x] (_Fri 01/01/21, 00:00:00_ ) - test0\n',
            ],
        ),
    ],
)
def test_move_complete(data, expected, tmpdir):
    with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
        lines = move(tmpdir, [0], True)
        assert lines == expected


@pytest.mark.parametrize(
    'data, expected', [
        (
            '### Todo\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' +
            '### In Progress\n' +
            '### Completed\n' +
            '- [x] (_Fri 01/01/21, 00:00:00_ ) - test1\n',
            [
                '### Todo\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n',
                '### In Progress\n',
                '### Completed\n',
            ],
        ),
    ],
)
def test_move_unmark_completed(data, expected, tmpdir):
    with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
        lines = move(tmpdir, [1], True)
        assert lines == expected


@pytest.mark.parametrize(
    'data, expected', [
        (
            '### Todo\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' +
            '### In Progress\n' +
            '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n' +
            '### Completed\n',
            [
                '### Todo\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n',
                '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test1\n',
                '### In Progress\n',
                '### Completed\n',
            ],
        ),
    ],
)
def test_move_inprogress(data, expected, tmpdir):
    with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
        lines = move(tmpdir, [1], False)
        assert lines == expected


def test_move_FileNotFound_SystemExit():
    with pytest.raises(SystemExit):
        move('dir_should_not_exist', [], False)


def test_move_IndexError_SystemExit(tmpdir):
    data = '### Todo\n' + \
           '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' + \
           '### In Progress\n' + \
           '### Completed\n'
    with pytest.raises(SystemExit):
        with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
            move(tmpdir, [100], True)


def test_move_missing_headers_SystemExit(tmpdir):
    with mock.patch('todome.main.open', mock.mock_open(read_data='')):
        with pytest.raises(SystemExit):
            move(tmpdir, [1], False)


def test_md_elements_to_unicode():
    line = md_elements_to_unicode('**test one instance**')
    assert line == '\033[1mtest one instance\033[0m'


def test_md_elements_to_unicode_mismatch():
    line = md_elements_to_unicode('**test one** instance**')
    assert line == '\033[1mtest one\033[0m instance**'


def test_read_print_file(tmpdir):
    data = '### Todo\n' + \
           '- [ ] (_Fri 01/01/21, 00:00:00_ ) - test0\n' + \
           '### In Progress\n' + \
           '### Completed\n'
    with mock.patch('todome.main.open', mock.mock_open(read_data=data)):
        read_print_file(tmpdir)


def test_read_print_file_FileNotFound_SystemExit():
    with pytest.raises(SystemExit):
        read_print_file('dir_should_not_exist')


@mock.patch('todome.main.virtualenv_check', return_value=True)
@mock.patch(
    'todome.main.parse_args', return_value=argparse.Namespace(
        add=None,
        remove=None,
        mark=None,
        create=False,
        progress=[],
    ),
)
@mock.patch('todome.main.open', mock.mock_open(read_data=''))
def test_main_venv_True(tmpdir, mock_virtualenv_bool):
    main()


@mock.patch('todome.main.virtualenv_check', return_value=False)
@mock.patch(
    'todome.main.parse_args', return_value=argparse.Namespace(
        add=None,
        remove=None,
        mark=None,
        create=False,
        progress=[],
    ),
)
@mock.patch('todome.main.open', mock.mock_open(read_data=''))
def test_main_venv_False(mock_virtualenv_bool, mock_args, tmpdir):
    main()


@mock.patch('todome.main.virtualenv_check', return_value=False)
@mock.patch('todome.main.create_markdown_file')
@mock.patch('todome.main.add')
@mock.patch('todome.main.remove')
@mock.patch('todome.main.move')
@mock.patch(
    'todome.main.parse_args', return_value=argparse.Namespace(
        add='test',
        remove=1,
        mark=1,
        create=True,
        progress=[1],
    ),
)
@mock.patch('todome.main.open', mock.mock_open(read_data=''))
def test_main_full_args(
    mock_virtualenv_bool,
    mock_create,
    mock_add,
    mock_remove,
    mock_move,
    tmpdir,
):
    main()
