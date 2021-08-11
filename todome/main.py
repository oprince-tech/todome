import argparse
import os
import re
import sys
from datetime import datetime


def create_markdown_file(path: str) -> None:
    try:
        open(f'{path}/TODO.md', 'x')
    except FileExistsError:
        sys.exit(f'{path}/TODO.md already exists')
    with open(f'{path}/TODO.md', 'w') as f:
        f.write('### Todo\n### In Progress\n### Completed\n')
    print(f'Creating {path}/TODO.md')


def write_lines(path: str, lines: list[str]) -> None:
    try:
        with open(f'{path}/TODO.md', 'w') as f:
            for line in lines:
                f.write(line)
    except FileNotFoundError as e:
         sys.exit(f'{type(e).__name__}: {e}')


def mark(entry: str, add_mark: bool) -> str:
    if add_mark:
        entry = re.sub(r'\[ \]', '[x]', entry)
    else:
        entry = re.sub(r'\[x\]', '[ ]', entry)

    return entry


def add(path: str, note: str) -> None:
    dt = datetime.now()
    fdt = dt.strftime('(_%a %m/%d/%y, %H:%M:%S_ )')
    entry = f'- [ ] {fdt} - {note}\n'

    try:
        with open(f'{path}/TODO.md', 'r+') as f:
            lines = f.readlines()
        in_progress_index = lines.index('### In Progress\n')
        lines.insert(in_progress_index, entry)
        write_lines(path, lines)
        print(f'Added: {note}')

    except FileNotFoundError as e:
         sys.exit(f'{type(e).__name__}: {e}')
    except ValueError as e:
        print(f'{type(e).__name__}: File is missing these lines: '
              f'### Todo, ### In Progress, and ### Completed')


def remove(path: str, lns: list[int]) -> None:
    try:
        with open(f'{path}/TODO.md', 'r+') as f:
            lines = f.readlines()
    except FileNotFoundError as e:
         sys.exit(f'{type(e).__name__}: {e}')

    entries = [x for x in lines if x.startswith('-')]

    for ln in sorted(lns, reverse=True):
        try:
            entry = entries[ln]
            entry_index = lines.index(entry)
            entry = entry.strip('\n')
            del lines[entry_index]
            print(f'Removed entry no. {ln}: {entry}')
        except IndexError as e:
            print(f'IndexError: {e}: {ln}')
    write_lines(path, lines)


def move(path: str, lns: list[int], complete: bool = False) -> None:
    try:
        with open(f'{path}/TODO.md', 'r+') as f:
            lines = f.readlines()
        in_progress_index = lines.index('### In Progress\n')
        completed_index = lines.index('### Completed\n')
        entries = [x for x in lines if x.startswith('-')]
        for ln in lns:
            entry = entries[ln]
            pos = lines.index(entry)
            if complete:
                # -m Flag selected
                if pos > completed_index:
                    # Marked as completed. Unmark and move to 'Todo'
                    del lines[pos]
                    unmarked_entry = mark(entry, add_mark=False)
                    lines.insert(in_progress_index, unmarked_entry)
                else:
                    # Not marked as completed. Mark and move to 'Completed'
                    del lines[pos]
                    marked_entry = mark(entry, add_mark=True)
                    lines.append(marked_entry)
            elif pos > in_progress_index and pos < completed_index:
                # Move to 'Todo'
                del lines[pos]
                lines.insert(in_progress_index, entry)
            else:
                # Move to 'In Progress'
                del lines[pos]
                lines.insert(completed_index-1, entry)

    except IndexError as e:
        print(f'{type(e).__name__}: Entry index out of range: {ln}')
    except FileNotFoundError as e:
         sys.exit(f'{type(e).__name__}: {e}')

    write_lines(path, lines)


def read_print_file(path: str) -> None:
    try:
        print(f'{path}/TODO.md')
        with open(f'{path}/TODO.md') as f:
            i = 0
            for line in f:
                if line[0] == '#' or len(line.strip()) == 0:
                    print(f'{line}', end='')
                else:
                    print(f'{i}\t{line}', end='')
                    i += 1
    except FileNotFoundError as e:
         sys.exit(
             f'{type(e).__name__}: {e}',
             f'Create a new TODO.md file with [todome -c]',
             )


def virtualenv_check() -> bool:
    return True if sys.prefix != sys.base_prefix else False


def parse_args():
    parser = argparse.ArgumentParser(
        description='Todo accesible anywhere in your terminal',
        usage='%(prog)s [options]',
    )
    parser.add_argument(
        '-a', '--add',
        help='Add a todo',
        type=str,
        nargs='?',
    )
    parser.add_argument(
        '-rm', '--remove',
        help='Remove a todo',
        type=int,
        nargs='*',
    )
    parser.add_argument(
        '-m', '--mark',
        help='Change checkmark status',
        type=int,
        nargs='*',
    )
    parser.add_argument(
        '-c', '--create',
        help='Create a note markdown file',
        action='store_true',
    )
    parser.add_argument(
        '-p', '--progress',
        help='Move in and out of In Progress',
        type=int,
        nargs='*',
    )

    args = parser.parse_args()
    return args

def main() -> int:
    args = parse_args()

    if virtualenv_check():
        save_path = os.path.dirname(sys.prefix)
    else:
        save_path = os.path.expanduser('~/Documents')

    if args.create:
        create_markdown_file(save_path)

    if args.add:
        add(save_path, args.add)

    if args.remove:
        remove(save_path, args.remove)

    if args.mark:
        move(save_path, args.mark, True)

    if args.progress:
        move(save_path, args.progress)

    read_print_file(save_path)

    return 0


if __name__ == '__main__':
    exit(main())